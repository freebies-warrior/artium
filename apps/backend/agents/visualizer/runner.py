from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from PIL import Image

from .config import VisualizerConfig
from .types import VisualizerResult, RoomQualityReport, CriticReport
from .pipeline_sequential import run_pipeline_sequential


def _ensure_parent_dir(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


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
    _ensure_parent_dir(out_path)

    # Prefer langgraph if available
    use_langgraph = os.getenv("VISUALIZER_USE_LANGGRAPH", "1") == "1"
    if use_langgraph:
        try:
            from .pipeline_langgraph import run_pipeline_langgraph  # noqa
            final = run_pipeline_langgraph(cfg, room_path, art_path)
            out_img = final["out_img"]
            used_enhancement = bool(final.get("used_enhancement", False))
            retries_used = int(final.get("retries_used", 0))
            room_quality = final["room_quality"]
            crit = final["critic"]
            placement = final.get("placement", None)
            appraisal = final.get("appraisal", None)
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

    out_img.save(out_path)

    return VisualizerResult(
        out_path=out_path,
        used_enhancement=used_enhancement,
        retries_used=retries_used,
        room_quality=room_quality,
        critic=crit,
        placement=placement,
        appraisal=appraisal,
    )
