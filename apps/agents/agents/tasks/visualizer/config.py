from __future__ import annotations

from pydantic import BaseModel, Field

from agents.core.settings import get_settings


class VisualizerConfig(BaseModel):
    # Gemini model used for image editing / multi-image fusion
    gemini_image_model: str = Field(default_factory=lambda: get_settings().VISUALIZER_GEMINI_MODEL)

    # Gemini model used for text-only judging/critique (can be same)
    gemini_text_model: str = Field(
        default_factory=lambda: get_settings().VISUALIZER_GEMINI_TEXT_MODEL
    )

    # If critic says "bad", allow a single retry by default
    max_retries: int = Field(default_factory=lambda: get_settings().VISUALIZER_MAX_RETRIES)

    # Threshold: if room judge says needs enhancement, we enhance
    enhance_if_low_quality: bool = Field(
        default_factory=lambda: get_settings().VISUALIZER_ENHANCE_IF_LOW_QUALITY
    )
