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

from visualizer.runner import visualize_installation  # noqa: E402
from visualizer.config import VisualizerConfig  # noqa: E402


class PreviewRequest(BaseModel):
    room_url: HttpUrl
    art_url: HttpUrl
    output_filename: Optional[str] = None  # default created in temp dir
    max_retries: Optional[int] = None
    image_model: Optional[str] = None
    text_model: Optional[str] = None
    no_enhance: bool = False


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

router = APIRouter(prefix = "/agents", tags = ["agents"])


def _download_to_temp(url: str, suffix: str) -> Path:
    resp = requests.get(url, timeout=30)
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Failed to download {url}: {resp.status_code}")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(resp.content)
    tmp.flush()
    tmp.close()
    return Path(tmp.name)


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/visualizer/config")
def get_config() -> dict:
    cfg = VisualizerConfig()
    return {
        "max_retries": cfg.max_retries,
        "gemini_image_model": cfg.gemini_image_model,
        "gemini_text_model": cfg.gemini_text_model,
        "enhance_if_low_quality": cfg.enhance_if_low_quality,
    }


@router.post("/visualizer/visualize_installation", response_model=PreviewResponse)
def preview(req: PreviewRequest) -> PreviewResponse:
    logger.info("preview request", extra={"room_url": str(req.room_url), "art_url": str(req.art_url)})

    # Prepare config overrides
    cfg = VisualizerConfig()
    if req.max_retries is not None:
        cfg.max_retries = req.max_retries
    if req.image_model is not None:
        cfg.gemini_image_model = req.image_model
    if req.text_model is not None:
        cfg.gemini_text_model = req.text_model
    if req.no_enhance:
        cfg.enhance_if_low_quality = False

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

    # Run visualizer
    try:
        result = visualize_installation(str(room_path), str(art_path), str(out_path), cfg=cfg)
    except Exception as exc:  # pragma: no cover - handled at runtime
        logger.exception("visualize_installation failed")
        raise HTTPException(status_code=500, detail=f"visualize_installation failed: {exc}")

    # Encode output image as base64 for transport; fetch remote if out_path is a URL
    out_path_str = str(result.out_path)
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
    appraisal_obj = getattr(result, "appraisal", None)
    appraisal_dict = None
    if appraisal_obj is not None:
        # AppraisalReport is a pydantic model; serialize to dict for response
        appraisal_dict = appraisal_obj.model_dump() if hasattr(appraisal_obj, "model_dump") else appraisal_obj.__dict__

    return PreviewResponse(
        out_path=str(result.out_path),
        preview_base64=f"data:image/jpeg;base64,{b64}",
        used_enhancement=result.used_enhancement,
        retries_used=result.retries_used,
        room_quality={
            "verdict": result.room_quality.verdict,
            "reasons": result.room_quality.reasons,
        },
        critic={
            "verdict": result.critic.verdict,
            "issues": result.critic.issues,
            "suggested_fix": result.critic.suggested_fix,
        },
        appraisal=appraisal_dict,
    )


# Convenience for local dev: `python agent.py`
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI

    demo_app = FastAPI(title="Visualizer Agent API", version="1.0")
    demo_app.include_router(router)
    uvicorn.run(demo_app, host="0.0.0.0", port=8000, reload=True)
