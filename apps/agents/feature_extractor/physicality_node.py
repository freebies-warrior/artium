from __future__ import annotations

import logging
from typing import Any, Dict

from langgraph.types import Command

from .llm_client import VisionLLMClient
from .prompt import build_physicality_prompt
from .types import FeatureState, Physicality

logger = logging.getLogger(__name__)


def physicality_node(llm: VisionLLMClient):
    def _node(state: FeatureState) -> Command:
        try:
            prompt = build_physicality_prompt(state["metadata"])
            raw: Dict[str, Any] = llm.infer_json(prompt=prompt, image_bytes=state["image_bytes"])
            parsed = Physicality.model_validate(raw).model_dump()
            logger.info("Physicality features extracted.")
            return Command(update={"vision_physicality": parsed}, goto="vision_aggregate_painting")
        except Exception as e:
            logger.error("Physicality agent failed", extra={"error_type": type(e).__name__})
            errs = list(state.get("errors", []))
            errs.append(f"physicality_agent_error: {e}")
            return Command(update={"errors": errs}, goto="vision_aggregate_painting")

    return _node
