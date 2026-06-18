import logging
from typing import Any, Dict

from langgraph.types import Command
from pydantic import ValidationError

from .llm_client import VisionLLMClient
from .prompt import build_material_prompt
from .types import FeatureState, MaterialComposition

logger = logging.getLogger(__name__)


def material_node(llm: VisionLLMClient):
    def node(state: FeatureState) -> Command:
        """Extract material composition from sculpture image."""
        try:
            metadata = state.get("metadata", {})
            image_bytes = state.get("image_bytes")

            if not image_bytes:
                raise ValueError("No image_bytes in state")

            prompt = build_material_prompt(metadata)
            result_json = llm.infer_json(
                prompt=prompt, image_jpeg_bytes=image_bytes, images_jpeg_bytes=[]
            )

            material = MaterialComposition(**result_json)

            logger.info(f"Material extraction successful: {material.primary_material}")

            return Command(
                update={"vision_material": material.model_dump()},
                goto="vision_aggregate_sculpture",
            )
        except ValidationError as e:
            error_msg = f"Material validation error: {e}"
            logger.error("Material validation error", extra={"error_type": type(e).__name__})
            return Command(update={"errors": [error_msg]}, goto="state_coordinator")
        except Exception as e:
            error_msg = f"Material extraction failed: {str(e)}"
            logger.error("Material extraction failed", extra={"error_type": type(e).__name__})
            return Command(update={"errors": [error_msg]}, goto="state_coordinator")

    return node
