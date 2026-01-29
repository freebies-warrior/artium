from __future__ import annotations

from typing import Any, Dict, TypedDict, Optional
from langgraph.graph import StateGraph, END

from PIL import Image

from .config import VisualizerConfig
from .client import GeminiClient
from .pipeline_sequential import (
    room_judge,
    room_enhance,
    composite_install,
    critic,
    _load_image,
)

class VizState(TypedDict, total=False):
    cfg: VisualizerConfig
    client: GeminiClient
    room_img: Image.Image
    art_img: Image.Image
    used_enhancement: bool
    retries_used: int
    room_quality: Any
    out_img: Image.Image
    critic: Any


def run_pipeline_langgraph(cfg: VisualizerConfig, room_path: str, art_path: str) -> Dict[str, Any]:
    """
    Returns a dict containing:
      out_img, used_enhancement, retries_used, room_quality, critic
    """
    if StateGraph is None:
        raise RuntimeError("langgraph is not installed; use sequential pipeline instead.")

    client = GeminiClient()
    state: VizState = {
        "cfg": cfg,
        "client": client,
        "room_img": _load_image(room_path),
        "art_img": _load_image(art_path),
        "used_enhancement": False,
        "retries_used": 0,
    }

    def node_judge(s: VizState) -> VizState:
        s["room_quality"] = room_judge(s["client"], s["cfg"], s["room_img"])
        return s

    def node_enhance(s: VizState) -> VizState:
        if s["cfg"].enhance_if_low_quality and s["room_quality"].verdict == "NEEDS_ENHANCEMENT":
            s["room_img"] = room_enhance(s["client"], s["cfg"], s["room_img"])
            s["used_enhancement"] = True
        return s

    def node_composite(s: VizState) -> VizState:
        s["out_img"] = composite_install(s["client"], s["cfg"], s["room_img"], s["art_img"])
        return s

    def node_critic(s: VizState) -> VizState:
        s["critic"] = critic(s["client"], s["cfg"], s["out_img"])
        return s

    def node_retry(s: VizState) -> VizState:
        s["retries_used"] += 1
        fix = s["critic"].suggested_fix or "Improve realism of scale, perspective, and shadow. Keep it photorealistic."
        s["out_img"] = composite_install(s["client"], s["cfg"], s["room_img"], s["art_img"], extra_fix_instruction=fix)
        return s

    def route_after_critic(s: VizState) -> str:
        if s["critic"].verdict == "PASS":
            return "end"
        if s["retries_used"] >= s["cfg"].max_retries:
            return "end"
        return "retry"

    g = StateGraph(VizState)
    g.add_node("judge", node_judge)
    g.add_node("enhance", node_enhance)
    g.add_node("composite", node_composite)
    g.add_node("critic", node_critic)
    g.add_node("retry", node_retry)

    g.set_entry_point("judge")
    g.add_edge("judge", "enhance")
    g.add_edge("enhance", "composite")
    g.add_edge("composite", "critic")

    g.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "retry": "retry",
            "end": END,
        },
    )

    g.add_edge("retry", "critic")

    app = g.compile()
    final = app.invoke(state)
    return final
