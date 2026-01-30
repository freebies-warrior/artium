import logging
from typing import Any, Dict

from pydantic import ValidationError
from langgraph.types import Command

from .types import FeatureState, Craftsmanship
from .llm_client import VisionLLMClient
from .prompt import build_craftsmanship_prompt

logger = logging.getLogger(__name__)


def craftsmanship_node(llm: VisionLLMClient):
    def node(state: FeatureState) -> Command:
        """Extract craftsmanship assessment from sculpture image."""
        try:
            metadata = state.get("metadata", {})
            image_bytes = state.get("image_bytes")
            
            if not image_bytes:
                raise ValueError("No image_bytes in state")
            
            prompt = build_craftsmanship_prompt(metadata)
            result_json = llm.infer_json(
                prompt=prompt,
                image_jpeg_bytes=image_bytes,
                images_jpeg_bytes=[]
            )
            
            craftsmanship = Craftsmanship(**result_json)
            
            logger.info(f"Craftsmanship extraction successful")
            
            return Command(
                update={
                    "vision_craftsmanship": craftsmanship.model_dump()
                },
                goto="vision_aggregate_sculpture"
            )
        except ValidationError as e:
            error_msg = f"Craftsmanship validation error: {e}"
            logger.error(error_msg)
            return Command(
                update={"errors": [error_msg]},
                goto="state_coordinator"
            )
        except Exception as e:
            error_msg = f"Craftsmanship extraction failed: {str(e)}"
            logger.error(error_msg)
            return Command(
                update={"errors": [error_msg]},
                goto="state_coordinator"
            )
    
    return node
