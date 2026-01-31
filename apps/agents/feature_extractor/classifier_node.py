import logging
from typing import Any, Dict

from langgraph.graph import END
from langgraph.types import Command

from .llm_client import VisionLLMClient
from .types import FeatureState

logger = logging.getLogger(__name__)


def artwork_classifier_node(llm: VisionLLMClient):
    """Classify whether the image is a painting, sculpture, or not an artwork."""

    def _node(state: FeatureState) -> Command:
        try:
            image_bytes = state.get("image_bytes")
            if not image_bytes:
                raise ValueError("No image_bytes in state")

            prompt = """You are an art classification expert. Analyze this image and determine:
1. Is this an artwork (painting or sculpture)?
2. If yes, is it a painting or a sculpture?

Respond with ONLY ONE of these exact values:
- "painting" if it's a painting, drawing, print, or 2D artwork
- "sculpture" if it's a 3D artwork (statue, sculpture, carving, installation)
- "NOT AN ARTWORK" if it's not art (e.g., photo, document, random object, person, landscape)

Return only the classification, nothing else."""

            classification = (
                llm.infer_text(prompt=prompt, image_bytes=image_bytes).strip().lower()
            )

            logger.info(f"Artwork classification: {classification}")

            # Validate classification
            if "painting" in classification:
                artwork_type = "painting"
            elif "sculpture" in classification:
                artwork_type = "sculpture"
            elif "not an artwork" in classification or "not art" in classification:
                artwork_type = "NOT AN ARTWORK"
            else:
                # Default to NOT AN ARTWORK if unclear
                logger.warning(
                    f"Unclear classification '{classification}', defaulting to NOT AN ARTWORK"
                )
                artwork_type = "NOT AN ARTWORK"

            # If not an artwork, end early
            if artwork_type == "NOT AN ARTWORK":
                return Command(update={"artwork_type": artwork_type}, goto=END)

            # Otherwise, route to state coordinator
            return Command(
                update={"artwork_type": artwork_type}, goto="state_coordinator"
            )

        except Exception as e:
            error_msg = f"Artwork classification failed: {str(e)}"
            logger.error(error_msg)
            return Command(
                update={"artwork_type": "NOT AN ARTWORK", "errors": [error_msg]},
                goto=END,
            )

    return _node
