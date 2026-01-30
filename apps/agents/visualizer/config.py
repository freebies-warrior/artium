from __future__ import annotations

from pydantic import BaseModel, Field
import os


class VisualizerConfig(BaseModel):
    # Gemini model used for image editing / multi-image fusion
    gemini_image_model: str = Field(
        default_factory=lambda: os.getenv("VISUALIZER_GEMINI_MODEL", "gemini-2.5-flash-image")
    )

    # Gemini model used for text-only judging/critique (can be same)
    gemini_text_model: str = Field(
        default_factory=lambda: os.getenv("VISUALIZER_GEMINI_TEXT_MODEL", "gemini-2.5-flash")
    )

    # If critic says "bad", allow a single retry by default
    max_retries: int = Field(default_factory=lambda: int(os.getenv("VISUALIZER_MAX_RETRIES", "1")))

    # Threshold: if room judge says needs enhancement, we enhance
    enhance_if_low_quality: bool = Field(
        default_factory=lambda: os.getenv("VISUALIZER_ENHANCE_IF_LOW_QUALITY", "1") == "1"
    )
