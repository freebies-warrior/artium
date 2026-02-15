"""FastAPI shim to expose the visualizer agent via HTTP.

Endpoints:
- POST /preview : enqueue visualize_installation on provided room/art URLs and return acknowledgement.
- GET  /health  : liveness check.

Start with:
    uvicorn agent:app --reload --port 8000
from this directory.
"""

from __future__ import annotations

import os
import base64
import logging
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
from dotenv import load_dotenv

import requests
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, HttpUrl
from enum import Enum

load_dotenv()

# Ensure agents package is importable when running from this folder
CURRENT_DIR = Path(__file__).resolve().parent
AGENTS_ROOT = CURRENT_DIR.parent  # .../apps/agents
if str(AGENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENTS_ROOT))
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080").rstrip("/")
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "").strip()

from feature_extractor.tools.image_tool import fetch_and_standardize_image  # noqa: E402
from feature_extractor.types import ArtworkMetadata, FeatureState  # noqa: E402
from feature_extractor.single_select import get_primary_image_index
from visualizer.config import VisualizerConfig  # noqa: E402
from visualizer.pipeline_langgraph import VizState  # noqa: E402
from visualizer.pipeline_sequential import _load_image  # noqa: E402
from visualizer.classify_node import is_valid_artwork_and_room  # noqa: E402
from visualizer.runner import _save_image  # noqa: E402

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
logging.basicConfig(level=logging.INFO)

# Create separate routers for each domain
system_router = APIRouter(tags=["system"])
visualizer_router = APIRouter(prefix="/agents/visualizer", tags=["visualizer"])
feature_extractor_router = APIRouter(prefix="/agents/feature_extractor", tags=["feature_extractor"])


def _download_to_temp(url: str, suffix: str) -> Path:
    resp = requests.get(url, timeout=30)
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Failed to download {url}: {resp.status_code}")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(resp.content)
    tmp.flush()
    tmp.close()
    return Path(tmp.name)


def _notify_backend_preview(
    job_id: str,
    status: JobStatus,
    result_description: Optional[str],
    error_message: Optional[str],
) -> None:
    url = f"{BACKEND_URL}/visualizations/{job_id}"
    payload = {
        "status": status.value,
        "result_description": result_description,
        "error_message": error_message,
    }

    headers = {}
    if INTERNAL_TOKEN:
        headers["Authorization"] = f"Bearer {INTERNAL_TOKEN}"

    try:
        resp = requests.put(url, json=payload, headers=headers, timeout=10)
        if resp.status_code >= 400:
            logger.warning(
                "failed to update visualizer job",
                extra={"job_id": job_id, "status": resp.status_code},
            )
    except Exception:
        logger.exception("failed to send visualizer job update", extra={"job_id": job_id})


def _notify_backend_feature_extraction(
    item_id: uuid.UUID,
    feature_json: dict[str, Any],
) -> None:
    sanitized_features = _sanitize_for_json(feature_json)
    if not isinstance(sanitized_features, dict):
        sanitized_features = {}
    url = f"{BACKEND_URL}/items/{item_id}/features"
    payload = {
        "features": sanitized_features,
    }

    headers = {}
    if INTERNAL_TOKEN:
        headers["Authorization"] = f"Bearer {INTERNAL_TOKEN}"

    try:
        resp = requests.put(url, json=payload, headers=headers, timeout=10)
        if resp.status_code >= 400:
            logger.warning(
                "failed to update feature extraction job",
                extra={"item_id": item_id, "status": resp.status_code},
            )
    except Exception:
        logger.exception("failed to send feature extraction job update", extra={"item_id": item_id})


def _sanitize_for_json(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray)):
        return None
    if isinstance(value, dict):
        return {
            key: _sanitize_for_json(val)
            for key, val in value.items()
            if not isinstance(val, (bytes, bytearray))
        }
    if isinstance(value, list):
        return [
            _sanitize_for_json(item) for item in value if not isinstance(item, (bytes, bytearray))
        ]
    if isinstance(value, tuple):
        return [_sanitize_for_json(item) for item in value]
    return value


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
        extra={"room_url": str(req.room_url), "art_url": str(req.art_url)},
    )

    cfg = VisualizerConfig()
    tmp_dir = Path(tempfile.mkdtemp())
    room_path = _download_to_temp(
        str(req.room_url), suffix=Path(req.room_url.path).suffix or ".jpeg"
    )
    art_path = _download_to_temp(str(req.art_url), suffix=Path(req.art_url.path).suffix or ".jpeg")

    if req.upload_image_url:
        base_name = Path(req.upload_image_url).name if req.upload_image_url else "preview.jpeg"
        if len(base_name) > 80:
            stem = Path(base_name).stem[:60]
            base_name = stem + Path(base_name).suffix
        # Ensure we have a file extension (default to .jpeg)
        ext = Path(base_name).suffix
        if not ext:
            base_name = f"{base_name}.jpeg"
        out_path = tmp_dir / base_name

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
        logger.exception("visualization failed")
    finally:
        logger.info("result_description: %s", result_description)
        _notify_backend_preview(
            req.job_id,
            status=status,
            result_description=result_description,
            error_message=error_message,
        )
        try:
            for f in tmp_dir.iterdir():
                f.unlink()
            tmp_dir.rmdir()
        except Exception:
            pass


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
    logger.info("feature extraction request", extra={"image_urls": str(req.image_get_urls)})

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
                logger.info(f"Running price valuation for {artwork_type}")

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
                    f"Price valuation complete: ${valuation_result.get('price_range', {}).get('mid', 0):,.2f}"
                )
            else:
                if artwork_type == "NOT_AN_ARTWORK":
                    logger.info("Skipping price valuation - input image not recognized as artwork")
                else:
                    logger.info(
                        f"Skipping price valuation - artwork_type '{artwork_type}' not supported"
                    )
        except Exception as valuation_exc:
            logger.exception(f"Price valuation failed: {valuation_exc}")
            # Continue even if valuation fails

        # Combine results
        combined_result = {
            **feature_json,
            "valuation": valuation_result if valuation_result else None,
        }

        del combined_result["image_bytes"]

        # # Build response (exclude image_bytes)
        # return FeatureExtractionResponse(
        #     metadata=final.get("metadata", {}),
        #     artwork_type=final.get("artwork_type", "UNKNOWN"),
        #     image_mode=final.get("image_mode", ""),
        #     image_size=list(final.get("image_size", (0, 0))),
        #     vision_features=final.get("vision_features"),
        #     market_features=final.get("market_features"),
        #     errors=final.get("errors", []),
        # )

    except Exception as exc:  # pragma: no cover - handled at runtime
        error_message = str(exc)
        logger.exception(f"feature extraction failed, {error_message}")
        combined_result = {}
    finally:
        logger.info("feature extraction complete")
        if not combined_result:
            combined_result = {}
        _notify_backend_feature_extraction(req.item_id, feature_json=combined_result)
