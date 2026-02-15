from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from PIL import Image

from core.settings import get_settings

from .config import VisualizerConfig
from .pipeline_sequential import run_pipeline_sequential
from .types import CriticReport, RoomQualityReport, VisualizerResult


def _save_image(out_img: Image.Image, out_path: str):
    """Save image to local path or upload via PUT if out_path is an HTTP(S) URL."""
    parsed = urlparse(out_path)
    if parsed.scheme in {"http", "https"}:
        buf = BytesIO()
        out_img.save(buf, format="JPEG")
        buf.seek(0)
        print("Uploading image to remote path")
        resp = requests.put(
            out_path,
            data=buf.getvalue(),
            headers={"Content-Type": "image/jpeg"},
            timeout=30,
        )
        print("Upload response:", resp.status_code, resp.text)
        resp.raise_for_status()
        # return out_path

    # return out_path


def visualize_installation(
    room_path: str,
    art_path: str,
    out_path: str,
    cfg: Optional[VisualizerConfig] = None,
) -> VisualizerResult:
    """
    High-level entrypoint.
    Will use LangGraph if installed, else sequential fallback.
    """
    cfg = cfg or VisualizerConfig()
    settings = get_settings()

    # Prefer langgraph if available
    use_langgraph = settings.VISUALIZER_USE_LANGGRAPH
    placement = None
    appraisal = None

    if use_langgraph:
        try:
            print("Trying langgraph pipeline")
            from .pipeline_langgraph import run_pipeline_langgraph  # noqa

            final = run_pipeline_langgraph(cfg, room_path, art_path)
            out_img = final["out_img"]
            used_enhancement = bool(final.get("used_enhancement", False))
            retries_used = int(final.get("retries_used", 0))
            room_quality = final["room_quality"]
            crit = final["critic"]
            placement = final.get("placement")
            appraisal = final.get("appraisal")
        except Exception as e:
            print(f"LangGraph pipeline failed with error: {e}")
            # fallback silently
            out_img, used_enhancement, retries_used, room_quality, crit = run_pipeline_sequential(
                cfg, room_path, art_path
            )
    else:
        print("LangGraph pipeline not used; falling back to sequential.")
        out_img, used_enhancement, retries_used, room_quality, crit = run_pipeline_sequential(
            cfg, room_path, art_path
        )

    saved_path = _save_image(out_img, out_path)

    return VisualizerResult(
        out_path=saved_path,
        used_enhancement=used_enhancement,
        retries_used=retries_used,
        room_quality=room_quality,
        critic=crit,
        placement=placement,
        appraisal=appraisal,
    )
