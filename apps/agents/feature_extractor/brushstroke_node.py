from __future__ import annotations

import logging
from typing import Any, Dict

from langgraph.types import Command

from .llm_client import VisionLLMClient
from .prompt import build_brushstroke_prompt
from .types import BrushstrokeDynamics, FeatureState

logger = logging.getLogger(__name__)


def brushstroke_node(llm: VisionLLMClient):
    def _node(state: FeatureState) -> Command:
        try:
            prompt = build_brushstroke_prompt(state["metadata"])
            raw: Dict[str, Any] = llm.infer_json(prompt=prompt, image_bytes=state["image_bytes"])
            parsed = BrushstrokeDynamics.model_validate(raw).model_dump()
            logger.info("Brushstroke features extracted.")
            return Command(update={"vision_brushstroke": parsed}, goto="vision_aggregate_painting")
        except Exception as e:
            logger.exception("Brushstroke agent failed: %s", e)
            errs = list(state.get("errors", []))
            errs.append(f"brushstroke_agent_error: {e}")
            return Command(update={"errors": errs}, goto="vision_aggregate_painting")

    return _node
