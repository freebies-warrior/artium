import logging
from typing import Any, Dict

from langgraph.types import Command
from pydantic import ValidationError

from .types import (
    Craftsmanship,
    FeatureState,
    Form,
    MaterialComposition,
    SculptureVisionFeatures,
    SurfaceFinish,
)

logger = logging.getLogger(__name__)


def vision_aggregate_sculpture_node():
    def node(state: FeatureState) -> Command:
        """Aggregate sculpture vision features from sub-extractions."""
        try:
            material_data = state.get("vision_material", {})
            form_data = state.get("vision_form", {})
            surface_data = state.get("vision_surface", {})
            craftsmanship_data = state.get("vision_craftsmanship", {})

            material = MaterialComposition(**material_data) if material_data else None
            form = Form(**form_data) if form_data else None
            surface = SurfaceFinish(**surface_data) if surface_data else None
            craftsmanship = Craftsmanship(**craftsmanship_data) if craftsmanship_data else None

            if not all([material, form, surface, craftsmanship]):
                raise ValueError("Missing one or more sub-features for aggregation")

            # Build justification from sub-notes
            notes = []
            if material.notes:
                notes.append(f"Material: {material.notes}")
            if form.notes:
                notes.append(f"Form: {form.notes}")
            if surface.notes:
                notes.append(f"Surface: {surface.notes}")
            if craftsmanship.notes:
                notes.append(f"Craftsmanship: {craftsmanship.notes}")

            justification = (
                " | ".join(notes)
                if notes
                else "Integrated assessment of material, form, surface, and craftsmanship."
            )

            aggregated = SculptureVisionFeatures(
                material=material,
                form=form,
                surface=surface,
                craftsmanship=craftsmanship,
                justification=justification,
            )

            logger.info(f"Sculpture vision aggregation successful.")

            return Command(
                update={"vision_features": aggregated.model_dump()},
                goto="state_coordinator",
            )
        except ValidationError as e:
            error_msg = f"Sculpture aggregation validation error: {e}"
            logger.error(
                "Sculpture aggregation validation error", extra={"error_type": type(e).__name__}
            )
            return Command(update={"errors": [error_msg]}, goto="state_coordinator")
        except Exception as e:
            error_msg = f"Sculpture aggregation failed: {str(e)}"
            logger.error("Sculpture aggregation failed", extra={"error_type": type(e).__name__})
            return Command(update={"errors": [error_msg]}, goto="state_coordinator")

    return node
