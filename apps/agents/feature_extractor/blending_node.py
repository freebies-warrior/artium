from __future__ import annotations

import logging
from typing import Any, Dict

from langgraph.types import Command

from .llm_client import VisionLLMClient
from .prompt import build_blending_prompt
from .types import BlendingMerging, FeatureState

logger = logging.getLogger(__name__)


def blending_node(llm: VisionLLMClient):
    def _node(state: FeatureState) -> Command:
        try:
            prompt = build_blending_prompt(state["metadata"])
            raw: Dict[str, Any] = llm.infer_json(prompt=prompt, image_bytes=state["image_bytes"])
            parsed = BlendingMerging.model_validate(raw).model_dump()
            logger.info("Blending features extracted.")
            return Command(update={"vision_blending": parsed}, goto="vision_aggregate_painting")
        except Exception as e:
            logger.error("Blending agent failed", extra={"error_type": type(e).__name__})
            errs = list(state.get("errors", []))
            errs.append(f"blending_agent_error: {e}")
            return Command(update={"errors": errs}, goto="vision_aggregate_painting")

    return _node
