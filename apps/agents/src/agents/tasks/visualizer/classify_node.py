"""Classification node for artwork and room detection."""

from __future__ import annotations

from typing import Any
from PIL import Image

from agents.core.constants import DEFAULT_GEMINI_TEXT_MODEL
from agents.core.types import ArtworkType, normalize_artwork_type

from .client import GeminiClient


def classify_artwork_and_room(
    artwork_image: Image.Image,
    room_image: Image.Image,
    model: str = DEFAULT_GEMINI_TEXT_MODEL,
) -> dict[str, Any]:
    """
    Classify whether first image is an artwork and second image is a room.

    Args:
        artwork_image: PIL Image of potential artwork
        room_image: PIL Image of potential room
        model: Gemini model to use

    Returns:
        Classification result dict with:
        - is_artwork: bool - whether first image is artwork
        - artwork_type: str - "painting", "sculpture", "drawing", "other", or "not_artwork"
        - is_room: bool - whether second image is a room
        - room_type: str - "interior", "gallery", "studio", "other", or "not_room"
        - confidence: float - overall confidence (0-1)
        - reasoning: str - explanation of classification
    """

    client = GeminiClient()

    prompt = """Analyze these two images and classify them:

1. FIRST IMAGE: Check if it's an artwork
   - If yes, identify the type: "painting", "sculpture", "drawing", or "other"
   - If no, return "not_artwork"

2. SECOND IMAGE: Check if it's a room/interior space
   - If yes, identify the type: "interior", "gallery", "studio", or "other"
   - If no, return "not_room"

Return a JSON object with:
{
    "is_artwork": boolean,
    "artwork_type": string,
    "is_room": boolean,
    "room_type": string,
    "confidence": float (0.0-1.0),
    "reasoning": string (brief explanation)
}"""

    result = client.generate_json(
        model=model,
        prompt=prompt,
        images=[artwork_image, room_image],
    )

    return result


def is_valid_artwork_and_room(
    artwork_image: Image.Image,
    room_image: Image.Image,
    model: str = DEFAULT_GEMINI_TEXT_MODEL,
) -> tuple[bool, bool | None, bool | None]:
    """
    Check if first image is artwork AND second image is a room.

    Args:
        artwork_image: PIL Image of potential artwork
        room_image: PIL Image of potential room
        model: Gemini model to use

    Returns:
        True if both conditions are met, False otherwise
    """
    result = classify_artwork_and_room(artwork_image, room_image, model)

    is_valid = (result.get("is_artwork") is True) and (result.get("is_room")) is True

    is_artwork = None
    is_room = None

    if is_valid:
        artwork_type = normalize_artwork_type(result.get("artwork_type"))
        is_artwork = artwork_type != ArtworkType.NOT_ARTWORK.value
        is_room = result.get("room_type") != "not_room"

    return is_valid, is_artwork, is_room
