"""Unified service for managing feature extraction and visualization graphs."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any

from PIL import Image

from agents.api.commands import FeatureExtractionJobCommand, PreviewJobCommand
from agents.core.adapters import HttpBackendCallbackClient
from agents.core.constants import DEFAULT_DOWNLOAD_TIMEOUT_SECONDS, DEFAULT_IMAGE_SUFFIX
from agents.core.ports import BackendCallbackClient
from agents.core.types import ArtworkType, JobStatus, normalize_artwork_type
from agents.core.utils.errors import redacted_exc_info
from agents.core.utils.files import download_to_temp_file
from agents.core.utils.http import loggable_url
from agents.tasks.feature_extractor.graph import build_graph
from agents.tasks.feature_extractor.llm_client import GeminiVisionClient
from agents.tasks.feature_extractor.service import build_initial_feature_state
from agents.tasks.feature_extractor.types import FeatureState
from agents.tasks.price_valuator.graph import build_valuation_graph
from agents.tasks.price_valuator.types import ValuationState
from agents.tasks.visualizer.client import GeminiClient
from agents.tasks.visualizer.config import VisualizerConfig
from agents.tasks.visualizer.pipeline_langgraph import build_visualization_graph
from agents.tasks.visualizer.service import load_preview_images, run_preview_with_graph

logger = logging.getLogger(__name__)


class AgentService:
    """Unified service for managing feature extraction, visualization, and price valuation graphs."""

    def __init__(self, *, callback_client: BackendCallbackClient | None = None):
        self.feature_graph = None
        self.visualizer_graph = None
        self.valuation_graph = None
        self.feature_client = None
        self.visualizer_client = None
        self.callback_client = callback_client or HttpBackendCallbackClient()

    def initialize(self):
        """Initialize all graphs and clients (called once at startup)."""
        logger.info("Initializing AgentService...")
        self.feature_client = GeminiVisionClient()
        self.feature_graph = build_graph(vision_llm=self.feature_client)
        self.visualizer_client = GeminiClient()
        self.visualizer_graph = build_visualization_graph()
        self.valuation_graph = build_valuation_graph()
        logger.info("AgentService initialized successfully.")

    def shutdown(self):
        """Clean up resources (called at shutdown)."""
        logger.info("Shutting down AgentService...")
        self.feature_graph = None
        self.visualizer_graph = None
        self.valuation_graph = None
        self.feature_client = None
        self.visualizer_client = None
        logger.info("AgentService shut down.")

    def extract_features(self, initial_state: FeatureState) -> FeatureState:
        """Extract features from artwork using the cached feature extraction graph."""
        if self.feature_graph is None:
            raise RuntimeError("AgentService not initialized. Call initialize() first.")

        logger.info("Extracting features...")
        result = self.feature_graph.invoke(initial_state)
        logger.info(f"Feature extraction complete. Artwork type: {result.get('artwork_type')}")
        return result

    def run_visualizer_preview(
        self,
        cfg: VisualizerConfig,
        room_img: Image.Image,
        art_img: Image.Image,
        upload_image_url: str | None,
    ) -> str:
        """Run visualizer preview flow using cached visualizer resources."""
        if self.visualizer_graph is None or self.visualizer_client is None:
            raise RuntimeError("AgentService not initialized. Call initialize() first.")

        logger.info("Running visualization pipeline...")
        result = run_preview_with_graph(
            cfg=cfg,
            room_img=room_img,
            art_img=art_img,
            upload_image_url=upload_image_url,
            visualizer_client=self.visualizer_client,
            visualizer_graph=self.visualizer_graph,
        )
        logger.info("Visualization complete.")
        return result

    def run_preview_job(self, req: PreviewJobCommand) -> None:
        logger.info(
            "preview request",
            extra={
                "room_url": loggable_url(req.room_url),
                "art_url": loggable_url(req.art_url),
            },
        )

        cfg = VisualizerConfig()
        room_url_path = Path(urlsplit(req.room_url).path)
        art_url_path = Path(urlsplit(req.art_url).path)
        status = JobStatus.FAILED
        result_description = None
        error_message = None
        room_path = None
        art_path = None
        room_img = None
        art_img = None

        try:
            room_path = download_to_temp_file(
                req.room_url,
                suffix=room_url_path.suffix or DEFAULT_IMAGE_SUFFIX,
                timeout=DEFAULT_DOWNLOAD_TIMEOUT_SECONDS,
            )
            art_path = download_to_temp_file(
                req.art_url,
                suffix=art_url_path.suffix or DEFAULT_IMAGE_SUFFIX,
                timeout=DEFAULT_DOWNLOAD_TIMEOUT_SECONDS,
            )
            room_img, art_img = load_preview_images(str(room_path), str(art_path))
            result_description = self.run_visualizer_preview(
                cfg=cfg,
                room_img=room_img,
                art_img=art_img,
                upload_image_url=req.upload_image_url,
            )
            status = JobStatus.SUCCEEDED
        except Exception as exc:
            error_message = str(exc)
            logger.exception(
                "visualization failed",
                extra={
                    "task_name": "visualizer.preview",
                    "job_id": req.job_id,
                    "error_type": type(exc).__name__,
                },
                exc_info=redacted_exc_info(exc, include_traceback=False),
            )
        finally:
            if room_img is not None:
                room_img.close()
            if art_img is not None:
                art_img.close()
            for path in (room_path, art_path):
                if path is not None:
                    try:
                        path.unlink()
                    except FileNotFoundError:
                        pass
            logger.info("result_description: %s", result_description)
            self.callback_client.update_visualization(
                req.job_id,
                status=status,
                result_description=result_description,
                error_message=error_message,
            )

    def run_feature_extraction_job(self, req: FeatureExtractionJobCommand) -> None:
        """Run feature extraction and valuation flow, then report result to backend."""
        logger.info(
            "feature extraction request",
            extra={"image_urls": [loggable_url(image_url) for image_url in req.image_get_urls]},
        )

        combined_result: dict[str, Any] | None = None
        try:
            initial_state, metadata, image_bytes = build_initial_feature_state(
                image_urls=list(req.image_get_urls),
                item_id=str(req.item_id),
                metadata=dict(req.metadata),
            )

            final = self.extract_features(initial_state)
            feature_json = final

            valuation_result = None
            try:
                artwork_type = normalize_artwork_type(str(final.get("artwork_type", "")))
                if artwork_type in (ArtworkType.PAINTING.value, ArtworkType.SCULPTURE.value):
                    logger.info("running price valuation", extra={"artwork_type": artwork_type})

                    valuation_state = {
                        "artwork_features": final,
                        "metadata": metadata,
                        "artwork_type": artwork_type,
                        "image_bytes": image_bytes,
                        "errors": [],
                    }

                    valuation_result = self.valuate_artwork(valuation_state)

                    logger.info(
                        "price valuation complete",
                        extra={"mid_price": valuation_result.get("price_range", {}).get("mid", 0)},
                    )
                else:
                    if artwork_type == ArtworkType.NOT_ARTWORK.value:
                        logger.info(
                            "Skipping price valuation - input image not recognized as artwork"
                        )
                    else:
                        logger.info(
                            "Skipping price valuation - artwork_type '%s' not supported",
                            artwork_type,
                        )
            except Exception as exc:
                logger.exception(
                    "price valuation failed",
                    extra={
                        "task_name": "feature_extractor.valuation",
                        "item_id": str(req.item_id),
                        "error_type": type(exc).__name__,
                    },
                    exc_info=redacted_exc_info(exc, include_traceback=False),
                )

            combined_result = {
                **feature_json,
                "valuation": valuation_result if valuation_result else None,
            }
            del combined_result["image_bytes"]

        except Exception as exc:
            logger.exception(
                "feature extraction failed",
                extra={
                    "task_name": "feature_extractor.extract",
                    "item_id": str(req.item_id),
                    "error_type": type(exc).__name__,
                },
                exc_info=redacted_exc_info(exc, include_traceback=False),
            )
        finally:
            logger.info("feature extraction complete")
            if combined_result is not None:
                self.callback_client.update_item_features(req.item_id, feature_json=combined_result)

    def valuate_artwork(self, state: ValuationState) -> ValuationState:
        """Run price valuation pipeline using the cached valuation graph."""
        if self.valuation_graph is None:
            raise RuntimeError("AgentService not initialized. Call initialize() first.")

        logger.info("Running price valuation pipeline...")
        result = self.valuation_graph.invoke(state)
        logger.info("Price valuation complete.")
        return result


# Global service instance
_agent_service: AgentService | None = None


def get_agent_service() -> AgentService:
    """Get the global agent service instance."""
    global _agent_service
    if _agent_service is None:
        raise RuntimeError("Agent service not initialized")
    return _agent_service


@asynccontextmanager
async def agent_service_lifespan():
    """Async context manager for agent service lifecycle."""
    global _agent_service

    # Startup
    _agent_service = AgentService()
    _agent_service.initialize()

    yield

    # Shutdown
    if _agent_service:
        _agent_service.shutdown()
        _agent_service = None
