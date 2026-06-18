from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, TypedDict


class FeatureState(TypedDict, total=False):
    # Input
    metadata: Dict[str, Any]
    artwork_type: str  # "painting" or "sculpture"

    # Image
    image_bytes: bytes
    image_mode: str
    image_size: Tuple[int, int]

    # Painting outputs
    vision_brushstroke: Dict[str, Any]
    vision_blending: Dict[str, Any]
    vision_physicality: Dict[str, Any]

    # Sculpture outputs
    vision_material: Dict[str, Any]
    vision_form: Dict[str, Any]
    vision_surface: Dict[str, Any]
    vision_craftsmanship: Dict[str, Any]

    # Aggregated vision features (domain-specific)
    vision_features: Dict[str, Any]

    # Market features (shared) - typically excluded from ingestion
    market_features: Dict[str, Any]

    # Control / Debug
    errors: List[str]
