from __future__ import annotations

import logging
from typing import Any, Dict, List

from langgraph.types import Command

from .types import (
    BlendingMerging,
    BrushstrokeDynamics,
    FeatureState,
    Physicality,
    VisionFeatures,
)

logger = logging.getLogger(__name__)


def _avg(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.5


def vision_aggregate_node():
    def _node(state: FeatureState) -> Command:
        try:
            missing = [
                key
                for key in ("vision_brushstroke", "vision_blending", "vision_physicality")
                if key not in state
            ]
            if missing:
                raise KeyError("Missing vision feature(s): " + ", ".join(sorted(missing)))

            brush = BrushstrokeDynamics.model_validate(state["vision_brushstroke"])
            blend = BlendingMerging.model_validate(state["vision_blending"])
            phys = Physicality.model_validate(state["vision_physicality"])

            notes = " ".join([n for n in [brush.notes, blend.notes, phys.notes] if n]).strip()
            if not notes:
                notes = "Extracted from visible cues across brushwork, edge handling, and material support."

            vf = VisionFeatures(
                brushstroke=brush,
                blending=blend,
                physicality=phys,
                justification=notes,
            ).model_dump()

            logger.info("Vision features aggregated.")
            return Command(update={"vision_features": vf}, goto="state_coordinator")
        except Exception as e:
            logger.error("Vision aggregate failed", extra={"error_type": type(e).__name__})
            errs = list(state.get("errors", []))
            errs.append(f"vision_aggregate_error: {e}")
            return Command(update={"errors": errs}, goto="state_coordinator")

    return _node
