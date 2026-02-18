"""Select primary/main image from multiple images."""

from __future__ import annotations

import io
from typing import Any
from PIL import Image

from .llm_client import VisionLLMClient


def select_primary_image(
    images_bytes: list[bytes],
    model: str = "gemini-2.5-flash",
) -> dict[str, Any]:
    """
    Analyze multiple images and select the primary/main view that best represents all others.

    Args:
        images: List of PIL Images to analyze
        model: Gemini model to use

    Returns:
        Dict with:
        - primary_index: int - index of the primary/main image (0-based)
        - primary_image_description: str - description of why this is the primary
        - analysis: list - analysis for each image
        - reasoning: str - overall reasoning
    """

    if not images_bytes:
        raise ValueError("Must provide at least one image")

    if len(images_bytes) == 1:
        return {
            "primary_index": 0,
            "primary_image_description": "Only image provided",
            "analysis": [{"index": 0, "quality": "only", "description": "Single image"}],
            "reasoning": "Single image selected as primary",
        }

    client = VisionLLMClient(model=model)

    prompt = f"""You are analyzing {len(images_bytes)} images of the same artwork/subject from different angles or conditions.

Your task: Identify which single image is the PRIMARY/MAIN VIEW that best represents and encompasses all the other images.

Consider:
- Clarity and sharpness
- Complete view of the subject
- Lighting and contrast quality
- Composition and framing
- How well it represents the full context
- Ability to convey the main characteristics

For each image, provide:
1. A brief quality assessment
2. How well it represents the overall subject
3. Any limitations or issues

Then identify the PRIMARY image (its 0-based index) that should be the main view.

Return JSON:
{{
    "primary_index": integer (0-based index),
    "primary_image_description": string (why this is primary),
    "analysis": [
        {{
            "index": integer,
            "representative_score": float (0-1)
        }}
    ],
    "reasoning": string
}}"""

    result = client.generate_json(
        prompt=prompt,
        images_jpeg_bytes=images_bytes,
    )

    # Validate the result
    if "primary_index" not in result:
        raise ValueError("LLM failed to identify primary_index")

    primary_idx = result.get("primary_index")
    if not isinstance(primary_idx, int) or primary_idx < 0 or primary_idx >= len(images_bytes):
        result = {
            "primary_index": 0,
        }
        # raise ValueError(f"Invalid primary_index: {primary_idx}")

    return result


def get_primary_image_index(
    images: list[bytes],
    model: str = "gemini-2.5-flash",
) -> int:
    """
    Simple wrapper to get just the primary image index.

    Args:
        images: List of PIL Images
        model: Gemini model to use

    Returns:
        Index of the primary image (0-based)
    """
    result = select_primary_image(images, model)
    return result["primary_index"]
