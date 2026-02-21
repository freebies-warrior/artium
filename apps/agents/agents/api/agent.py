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
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, Field, HttpUrl, model_validator

from agents.tasks.visualizer.config import VisualizerConfig

from .commands import FeatureExtractionJobCommand, PreviewJobCommand
from .service import get_agent_service


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
    item_id: uuid.UUID
    image_keys: List[str] = Field(min_length=1)
    image_get_urls: List[HttpUrl] = Field(min_length=1)
    callback_url: Optional[HttpUrl] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_image_list_lengths(self) -> "FeatureExtractionRequest":
        if len(self.image_keys) != len(self.image_get_urls):
            raise ValueError("image_keys and image_get_urls must have the same length")
        return self


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
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


# Create separate routers for each domain
system_router = APIRouter(tags=["system"])
visualizer_router = APIRouter(prefix="/agents/visualizer", tags=["visualizer"])
feature_extractor_router = APIRouter(prefix="/agents/feature_extractor", tags=["feature_extractor"])


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
    service = get_agent_service()
    command = PreviewJobCommand.from_request(req)
    service.run_preview_job(command)


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


def _extract_features(req: FeatureExtractionRequest) -> None:
    service = get_agent_service()
    command = FeatureExtractionJobCommand.from_request(req)
    service.run_feature_extraction_job(command)
