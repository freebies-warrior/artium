"""FastAPI shim to expose the visualizer agent via HTTP.

Endpoints:
- POST /preview : run visualize_installation on provided room/art URLs and return summary + base64 image.
- GET  /health  : liveness check.

Start with:
    uvicorn agent:app --reload --port 8000
from this directory.
"""

from __future__ import annotations

import base64
import logging
import sys
import tempfile
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

# Ensure agents package is importable when running from this folder
CURRENT_DIR = Path(__file__).resolve().parent
AGENTS_ROOT = CURRENT_DIR.parent  # .../apps/agents
if str(AGENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENTS_ROOT))

from visualizer.config import VisualizerConfig  # noqa: E402
from visualizer.pipeline_langgraph import VizState  # noqa: E402
from visualizer.pipeline_sequential import _load_image  # noqa: E402
from feature_extractor.types import FeatureState, ArtworkMetadata  # noqa: E402
from feature_extractor.tools.image_tool import fetch_and_standardize_image  # noqa: E402
from .service import get_agent_service  # noqa: E402


class PreviewRequest(BaseModel):
    room_url: HttpUrl
    art_url: HttpUrl
    output_filename: Optional[str] = None  # default created in temp dir
    max_retries: Optional[int] = None
    image_model: Optional[str] = None
    text_model: Optional[str] = None
    no_enhance: bool = False


class FeatureExtractionRequest(BaseModel):
    image_url: HttpUrl
    title: Optional[str] = "Unknown"
    author: Optional[str] = "Unknown"
    year: Optional[str] = None
    medium_hint: Optional[str] = None


class FeatureExtractionResponse(BaseModel):
    metadata: dict
    artwork_type: str
    image_mode: str
    image_size: list
    vision_features: Optional[dict] = None
    market_features: Optional[dict] = None
    errors: list


class PreviewResponse(BaseModel):
    out_path: str
    preview_base64: str
    used_enhancement: bool
    retries_used: int
    room_quality: dict
    critic: dict
    appraisal: Optional[dict] = None


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Create separate routers for each domain
system_router = APIRouter(tags=["system"])
visualizer_router = APIRouter(prefix="/agents/visualizer", tags=["visualizer"])
feature_extractor_router = APIRouter(prefix="/agents/feature-extractor", tags=["feature-extractor"])


def _download_to_temp(url: str, suffix: str) -> Path:
    resp = requests.get(url, timeout=30)
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Failed to download {url}: {resp.status_code}")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(resp.content)
    tmp.flush()
    tmp.close()
    return Path(tmp.name)


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


@visualizer_router.post("/visualize_installation", response_model=PreviewResponse)
def preview(req: PreviewRequest) -> PreviewResponse:
    logger.info("preview request", extra={"room_url": str(req.room_url), "art_url": str(req.art_url)})

    # Prepare config overrides
    cfg = VisualizerConfig()

    # Download images to temp files
    tmp_dir = Path(tempfile.mkdtemp())
    room_path = _download_to_temp(str(req.room_url), suffix=Path(req.room_url.path).suffix or ".jpeg")
    art_path = _download_to_temp(str(req.art_url), suffix=Path(req.art_url.path).suffix or ".jpeg")

    # Decide output path (support presigned URL; otherwise shorten local filename)
    if req.output_filename and urlparse(req.output_filename).scheme in {"http", "https"}:
        out_path = req.output_filename
    else:
        base_name = Path(req.output_filename).name if req.output_filename else "preview.jpeg"
        # Trim excessively long filenames
        if len(base_name) > 80:
            stem = Path(base_name).stem[:60]
            base_name = stem + Path(base_name).suffix
        out_path = tmp_dir / base_name

    # Run visualizer using cached service
    try:
        viz_service = get_agent_service()
        state: VizState = {
            "cfg": cfg,
            "client": viz_service.visualizer_client,
            "room_img": _load_image(str(room_path)),
            "art_img": _load_image(str(art_path)),
            "used_enhancement": False,
            "retries_used": 0,
        }
        result = viz_service.visualize(state)
        
        # Save output to file
        if not urlparse(str(out_path)).scheme in {"http", "https"}:
            result["out_img"].save(str(out_path))
    except Exception as exc:  # pragma: no cover - handled at runtime
        logger.exception("visualization failed")
        raise HTTPException(status_code=500, detail=f"visualization failed: {exc}")

    # Encode output image as base64 for transport; fetch remote if out_path is a URL
    out_path_str = str(out_path)
    parsed_out = urlparse(out_path_str)
    if parsed_out.scheme in {"http", "https"}:
        resp = requests.get(out_path_str, timeout=30)
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Failed to fetch output from {out_path_str}: {resp.status_code}")
        data = resp.content
    else:
        data = Path(out_path_str).read_bytes()
    b64 = base64.b64encode(data).decode()

    # Build response
    appraisal_obj = result.get("appraisal")
    appraisal_dict = None
    if appraisal_obj is not None:
        # AppraisalReport is a pydantic model; serialize to dict for response
        appraisal_dict = appraisal_obj.model_dump() if hasattr(appraisal_obj, "model_dump") else appraisal_obj.__dict__

    return PreviewResponse(
        out_path=str(out_path),
        preview_base64=f"data:image/jpeg;base64,{b64}",
        used_enhancement=result.get("used_enhancement", False),
        retries_used=result.get("retries_used", 0),
        room_quality={
            "verdict": result["room_quality"].verdict,
            "reasons": result["room_quality"].reasons,
        },
        critic={
            "verdict": result["critic"].verdict,
            "issues": result["critic"].issues,
            "suggested_fix": result["critic"].suggested_fix,
        },
        appraisal=appraisal_dict,
    )


@feature_extractor_router.post("/extract", response_model=FeatureExtractionResponse)
def extract_features(req: FeatureExtractionRequest) -> FeatureExtractionResponse:
    """Extract visual and market features from artwork image. Automatically determines if painting or sculpture."""
    logger.info("feature extraction request", extra={"image_url": str(req.image_url)})
    
    try:
        # Prepare metadata
        md = ArtworkMetadata(
            title=req.title or "Unknown",
            author=req.author or "Unknown",
            year=req.year,
            medium_hint=req.medium_hint,
        ).model_dump()
        
        # Fetch and standardize image
        image_bytes, image_mode, image_size = fetch_and_standardize_image(str(req.image_url), target_size=(1024, 1024))
        
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
        
        # Build response (exclude image_bytes)
        return FeatureExtractionResponse(
            metadata=final.get("metadata", {}),
            artwork_type=final.get("artwork_type", "UNKNOWN"),
            image_mode=final.get("image_mode", ""),
            image_size=list(final.get("image_size", (0, 0))),
            vision_features=final.get("vision_features"),
            market_features=final.get("market_features"),
            errors=final.get("errors", []),
        )
    
    except Exception as exc:
        logger.exception("Feature extraction failed")
        raise HTTPException(status_code=500, detail=f"Feature extraction failed: {exc}")


# Convenience for local dev: `python agent.py`
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI

    demo_app = FastAPI(title="Agents API", version="1.0")
    demo_app.include_router(system_router)
    demo_app.include_router(visualizer_router)
    demo_app.include_router(feature_extractor_router)
    uvicorn.run(demo_app, host="0.0.0.0", port=8000, reload=True)
