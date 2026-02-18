"""FastAPI shim to expose the visualizer agent via HTTP.

Endpoints:
- POST /preview : enqueue visualize_installation on provided room/art URLs and return acknowledgement.
- GET  /health  : liveness check.

Start with:
    uvicorn agent:app --reload --port 8000
from this directory.
"""

from __future__ import annotations

import base64
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from enum import Enum

from agents.core.settings import get_settings
from agents.core.utils.files import cleanup_directory, download_to_temp_file
from agents.core.utils.http import internal_auth_headers, loggable_url, put_json
from agents.core.utils.json import sanitize_for_json

from agents.tasks.feature_extractor.single_select import get_primary_image_index
from agents.tasks.feature_extractor.tools.image_tool import fetch_and_standardize_image  # noqa: E402
from agents.tasks.feature_extractor.types import ArtworkMetadata, FeatureState  # noqa: E402
from agents.tasks.visualizer.classify_node import is_valid_artwork_and_room  # noqa: E402
from agents.tasks.visualizer.config import VisualizerConfig  # noqa: E402
from agents.tasks.visualizer.pipeline_langgraph import VizState  # noqa: E402
from agents.tasks.visualizer.pipeline_sequential import _load_image  # noqa: E402
from agents.tasks.visualizer.runner import _save_image  # noqa: E402

from .service import get_agent_service  # noqa: E402


class ItemDimensions(BaseModel):
    width: int
    height: int


class VisualizerRequest(BaseModel):
    room_url: HttpUrl
    art_url: HttpUrl
    upload_image_url: Optional[str] = None  # default created in temp dir
    upload_image_key: Optional[str] = None
    item_dimensions: Optional[ItemDimensions] = None
    job_id: str


class FeatureExtractionRequest(BaseModel):
    item_id: Optional[uuid.UUID] = None
    image_keys: List[str]
    image_get_urls: List[HttpUrl]
    callback_url: Optional[HttpUrl] = None
    metadata: Dict[str, Any] = {}


class FeatureExtractionResponse(BaseModel):
    metadata: dict
    artwork_type: str
    image_mode: str
    image_size: list
    vision_features: Optional[dict] = None
    market_features: Optional[dict] = None
    errors: list


class AsyncPreviewResponse(BaseModel):
    ok: bool = True
    job_id: str


class AsyncFeatureExtractionResponse(BaseModel):
    ok: bool = True


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


logger = logging.getLogger(__name__)

# Create separate routers for each domain
system_router = APIRouter(tags=["system"])
visualizer_router = APIRouter(prefix="/agents/visualizer", tags=["visualizer"])
feature_extractor_router = APIRouter(prefix="/agents/feature_extractor", tags=["feature_extractor"])


def _download_to_temp(url: str, suffix: str) -> Path:
    return download_to_temp_file(url, suffix=suffix, timeout=30.0)


def _notify_backend_preview(
    job_id: str,
    status: JobStatus,
    result_description: Optional[str],
    error_message: Optional[str],
) -> None:
    settings = get_settings()
    url = f"{settings.backend_url}/visualizations/{job_id}"
    payload = {
        "status": status.value,
        "result_description": result_description,
        "error_message": error_message,
    }

    headers = internal_auth_headers(settings.INTERNAL_TOKEN)

    try:
        resp = put_json(url, payload, headers=headers, timeout=10.0)
        if resp.status_code >= 400:
            logger.warning(
                "failed to update visualizer job",
                extra={"job_id": job_id, "status": resp.status_code, "url": loggable_url(url)},
            )
    except Exception as exc:
        logger.error(
            "failed to send visualizer job update",
            extra={
                "job_id": job_id,
                "url": loggable_url(url),
                "error_type": type(exc).__name__,
            },
        )


def _notify_backend_feature_extraction(
    item_id: uuid.UUID,
    feature_json: dict[str, Any],
) -> None:
    settings = get_settings()
    sanitized_features = sanitize_for_json(feature_json)
    if not isinstance(sanitized_features, dict):
        sanitized_features = {}
    url = f"{settings.backend_url}/items/{item_id}/features"
    payload = {
        "features": sanitized_features,
    }

    headers = internal_auth_headers(settings.INTERNAL_TOKEN)

    try:
        resp = put_json(url, payload, headers=headers, timeout=10.0)
        if resp.status_code >= 400:
            logger.warning(
                "failed to update feature extraction job",
                extra={"item_id": item_id, "status": resp.status_code, "url": loggable_url(url)},
            )
    except Exception as exc:
        logger.error(
            "failed to send feature extraction job update",
            extra={
                "item_id": item_id,
                "url": loggable_url(url),
                "error_type": type(exc).__name__,
            },
        )


@system_router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@visualizer_router.get("/config")
def get_config() -> dict:
    cfg = VisualizerConfig()
    return {
        "max_retries": cfg.max_retries,
        "gemini_image_model": cfg.gemini_image_model,
        "gemini_text_model": cfg.gemini_text_model,
        "enhance_if_low_quality": cfg.enhance_if_low_quality,
    }


def _run_preview(req: VisualizerRequest) -> None:
    logger.info(
        "preview request",
        extra={
            "room_url": loggable_url(str(req.room_url)),
            "art_url": loggable_url(str(req.art_url)),
        },
    )

    cfg = VisualizerConfig()
    tmp_dir = Path(tempfile.mkdtemp())
    room_path = _download_to_temp(
        str(req.room_url), suffix=Path(req.room_url.path).suffix or ".jpeg"
    )
    art_path = _download_to_temp(str(req.art_url), suffix=Path(req.art_url.path).suffix or ".jpeg")

    status = JobStatus.FAILED
    result_description = None
    error_message = None

    room_img = _load_image(str(room_path))
    art_img = _load_image(str(art_path))

    try:
        valid, is_artwork, is_room = is_valid_artwork_and_room(art_img, room_img)
        if not valid:
            if not is_artwork and not is_room:
                raise ValueError(
                    "First image is not recognized as an artwork and second image is not recognized as a room."
                )
            if not is_artwork:
                raise ValueError("First image is not recognized as an artwork.")
            if not is_room:
                raise ValueError("Second image is not recognized as a room.")

        viz_service = get_agent_service()
        state: VizState = {
            "cfg": cfg,
            "client": viz_service.visualizer_client,
            "room_img": room_img,
            "art_img": art_img,
            "used_enhancement": False,
            "retries_used": 0,
        }
        result = viz_service.visualize(state)
        _save_image(result["out_img"], req.upload_image_url)

        result_description = result["appraisal"].summary

        status = JobStatus.SUCCEEDED
    except Exception as exc:  # pragma: no cover - handled at runtime
        error_message = str(exc)
        logger.error(
            "visualization failed",
            extra={"job_id": req.job_id, "error_type": type(exc).__name__},
        )
    finally:
        logger.info("result_description: %s", result_description)
        _notify_backend_preview(
            req.job_id,
            status=status,
            result_description=result_description,
            error_message=error_message,
        )
        cleanup_directory(tmp_dir)


@visualizer_router.post("/visualize_installation", response_model=AsyncPreviewResponse)
def preview(req: VisualizerRequest, background_tasks: BackgroundTasks) -> AsyncPreviewResponse:
    background_tasks.add_task(_run_preview, req)
    return AsyncPreviewResponse(job_id=req.job_id)


@feature_extractor_router.post("/extract", response_model=AsyncFeatureExtractionResponse)
def extract_features(
    req: FeatureExtractionRequest, background_tasks: BackgroundTasks
) -> AsyncFeatureExtractionResponse:
    background_tasks.add_task(_extract_features, req)
    return AsyncFeatureExtractionResponse()


def _extract_features(req: FeatureExtractionRequest) -> FeatureExtractionResponse:
    """Extract visual and market features from artwork image. Automatically determines if painting or sculpture."""
    logger.info(
        "feature extraction request",
        extra={"image_urls": [loggable_url(str(image_url)) for image_url in req.image_get_urls]},
    )

    try:
        selected_index = get_primary_image_index(
            images=[
                fetch_and_standardize_image(str(image_url), target_size=(512, 512))[0]
                for image_url in req.image_get_urls
            ]
        )

        image_url = req.image_get_urls[selected_index]

        # Prepare metadata
        md = ArtworkMetadata(
            item_id=str(req.item_id),
            title=req.metadata.get("title", "Unknown"),
            author=req.metadata.get("author", "Unknown"),
            year=str(req.metadata.get("year", "Unknown")),
            medium_hint=req.metadata.get("medium_hint", "Unknown"),
        ).model_dump()

        # Fetch and standardize image
        image_bytes, image_mode, image_size = fetch_and_standardize_image(
            str(image_url), target_size=(1024, 1024)
        )

        # Build initial state (artwork_type will be determined by classifier node)
        initial_state: FeatureState = {
            "metadata": md,
            "image_bytes": image_bytes,
            "image_mode": image_mode,
            "image_size": image_size,
            "errors": [],
        }

        # Use cached graph from agent service
        service = get_agent_service()
        final = service.extract_features(initial_state)

        feature_json = final

        # Run price valuation pipeline
        valuation_result = None
        try:
            artwork_type = final.get("artwork_type", "").lower()
            if artwork_type in ("painting", "sculpture"):
                logger.info("running price valuation", extra={"artwork_type": artwork_type})

                # Build valuation state
                valuation_state = {
                    "artwork_features": final,
                    "metadata": md,
                    "artwork_type": artwork_type,
                    "image_bytes": image_bytes,
                    "errors": [],
                }

                # Run valuation through service (graph is cached)
                valuation_result = service.valuate_artwork(valuation_state)

                logger.info(
                    "price valuation complete",
                    extra={"mid_price": valuation_result.get("price_range", {}).get("mid", 0)},
                )
            else:
                if artwork_type == "NOT_AN_ARTWORK":
                    logger.info("Skipping price valuation - input image not recognized as artwork")
                else:
                    logger.info(
                        "Skipping price valuation - artwork_type '%s' not supported",
                        artwork_type,
                    )
        except Exception as exc:
            logger.error(
                "price valuation failed",
                extra={
                    "item_id": str(req.item_id),
                    "error_type": type(exc).__name__,
                },
            )
            # Continue even if valuation fails

        # Combine results
        combined_result = {
            **feature_json,
            "valuation": valuation_result if valuation_result else None,
        }

        del combined_result["image_bytes"]

    except Exception as exc:  # pragma: no cover - handled at runtime
        logger.error(
            "feature extraction failed",
            extra={
                "item_id": str(req.item_id),
                "error_type": type(exc).__name__,
            },
        )
        combined_result = {}
    finally:
        logger.info("feature extraction complete")
        if not combined_result:
            combined_result = {}
        _notify_backend_feature_extraction(req.item_id, feature_json=combined_result)
