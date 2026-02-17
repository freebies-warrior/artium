from __future__ import annotations

import logging
from typing import Any, Dict, Optional, TypedDict

from langgraph.graph import END, StateGraph
from PIL import Image

from .client import GeminiClient
from .config import VisualizerConfig
from .pipeline_sequential import (
    _load_image,
    appraise_installation,
    composite_install,
    critic,
    locate_artwork,
    room_enhance,
    room_judge,
)

logger = logging.getLogger(__name__)


class VizState(TypedDict, total=False):
    cfg: VisualizerConfig
    client: GeminiClient
    room_img: Image.Image  # current img
    art_img: Image.Image
    used_enhancement: bool
    retries_used: int
    room_quality: Any
    out_img: Image.Image  # composite img
    critic: Any
    placement: Any
    appraisal: Any


def build_visualization_graph():
    """Build and compile the visualization graph (called once at startup)."""

    def node_judge(s: VizState) -> VizState:
        logger.debug("visualizer step", extra={"step": "judge"})
        s["room_quality"] = room_judge(s["client"], s["cfg"], s["room_img"])
        return s

    def node_enhance(s: VizState) -> VizState:
        logger.debug("visualizer step", extra={"step": "enhance"})
        if s["cfg"].enhance_if_low_quality and s["room_quality"].verdict == "NEEDS_ENHANCEMENT":
            s["room_img"] = room_enhance(s["client"], s["cfg"], s["room_img"])
            s["used_enhancement"] = True
        return s

    def node_composite(s: VizState) -> VizState:
        logger.debug("visualizer step", extra={"step": "composite"})
        s["out_img"] = composite_install(s["client"], s["cfg"], s["room_img"], s["art_img"])
        s["placement"] = locate_artwork(s["client"], s["cfg"], s["room_img"], s["out_img"])
        return s

    def node_critic(s: VizState) -> VizState:
        logger.debug("visualizer step", extra={"step": "critic"})
        s["critic"] = critic(s["client"], s["cfg"], s["out_img"])
        return s

    def node_retry(s: VizState) -> VizState:
        logger.debug("visualizer step", extra={"step": "retry"})
        s["retries_used"] += 1
        fix = (
            s["critic"].suggested_fix
            or "Improve realism of scale, perspective, and shadow. Keep it photorealistic. Do not remove anything from the original room."
        )
        s["out_img"] = composite_install(
            s["client"],
            s["cfg"],
            s["room_img"],
            s["art_img"],
            extra_fix_instruction=fix,
        )
        s["placement"] = locate_artwork(s["client"], s["cfg"], s["room_img"], s["out_img"])
        return s

    def node_appraisal(s: VizState) -> VizState:
        logger.debug("visualizer step", extra={"step": "appraisal"})
        s["appraisal"] = appraise_installation(s["client"], s["cfg"], s["out_img"], s["placement"])
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
    g.add_node("appraisal", node_appraisal)
    g.set_entry_point("judge")
    g.add_edge("judge", "enhance")
    g.add_edge("enhance", "composite")
    g.add_edge("composite", "critic")

    g.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "retry": "retry",
            "end": "appraisal",
        },
    )

    g.add_edge("retry", "critic")
    g.add_edge("appraisal", END)

    return g.compile()


def run_pipeline_langgraph(cfg: VisualizerConfig, room_path: str, art_path: str) -> Dict[str, Any]:
    """
    This is deprecated; use VisualizerService instead. Only used for testing using CLI

    Returns a dict containing:
      out_img, used_enhancement, retries_used, room_quality, critic

    Note: Consider using VisualizerService for production to cache the graph.
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

    app = build_visualization_graph()
    final = app.invoke(state)
    return final
