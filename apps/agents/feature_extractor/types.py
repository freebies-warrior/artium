from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, Optional, Tuple, TypedDict

from pydantic import BaseModel, Field


class ArtworkMetadata(BaseModel):
    title: str = "Unknown"
    author: str = "Unknown"
    year: Optional[str] = None
    medium_hint: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class BrushstrokeDynamics(BaseModel):
    impasto: float = Field(
        ge=0, le=1, description="Likelihood of thick paint / raised texture"
    )
    glazing: float = Field(
        ge=0, le=1, description="Likelihood of thin layered translucency"
    )
    stippling: float = Field(
        ge=0, le=1, description="Likelihood of dot-like application"
    )
    notes: str = ""


class BlendingMerging(BaseModel):
    sfumato: float = Field(ge=0, le=1, description="Soft transitions / smokiness")
    hard_edge: float = Field(
        ge=0, le=1, description="Crisp boundaries / hard-edge abstraction"
    )
    notes: str = ""


class Physicality(BaseModel):
    medium_detected: str = Field(
        description="e.g., Oil, Acrylic, Watercolor, Mixed media"
    )
    support_detected: str = Field(description="e.g., Canvas, Wood panel, Paper")
    surface_texture: str = Field(
        description="e.g., canvas weave visible, smooth gesso, wood grain"
    )
    notes: str = ""


class VisionFeatures(BaseModel):
    brushstroke: BrushstrokeDynamics
    blending: BlendingMerging
    physicality: Physicality
    justification: str = Field(
        description="Short, expert justification grounded in visible cues"
    )


# Sculpture-specific models
class MaterialComposition(BaseModel):
    primary_material: str = Field(
        description="e.g., Marble, Bronze, Stone, Wood, Resin"
    )
    secondary_materials: Optional[str] = Field(
        default=None, description="e.g., Granite, Patina, Gold leaf, Paint"
    )
    material_confidence: float = Field(
        ge=0, le=1, description="Confidence in material identification"
    )
    notes: str = ""


class Form(BaseModel):
    shape_description: str = Field(
        description="Visual description of overall form and composition"
    )
    composition_balance: float = Field(
        ge=0, le=1, description="Assessment of visual balance and proportions"
    )
    notes: str = ""


class SurfaceFinish(BaseModel):
    finish_type: str = Field(description="e.g., Polished, Matte, Weathered, Patinated")
    surface_quality: float = Field(
        ge=0, le=1, description="Quality and condition of surface"
    )
    visible_damage: str = Field(
        default="", description="e.g., Cracks, weathering, repairs"
    )
    notes: str = ""


class Craftsmanship(BaseModel):
    detail_level: str = Field(
        description="Assessment of detail and precision in carving/casting"
    )
    technique_visible: str = Field(
        description="e.g., Chisel marks, casting seams, finishing methods"
    )
    quality_assessment: float = Field(
        ge=0, le=1, description="Overall execution quality"
    )
    notes: str = ""


class SculptureVisionFeatures(BaseModel):
    material: MaterialComposition
    form: Form
    surface: SurfaceFinish
    craftsmanship: Craftsmanship
    justification: str = Field(
        description="Short, expert justification grounded in visible cues"
    )


class MarketFeatures(BaseModel):
    institutional_standing: Dict[str, Any] = Field(
        default_factory=dict,
        description="Signals like museum shows, biennales, collections, galleries",
    )
    auction_velocity: Dict[str, Any] = Field(
        default_factory=dict,
        description="Signals like frequency at Christie’s/Sotheby’s, sell-through, lots/yr",
    )
    sentiment_hype: Dict[str, Any] = Field(
        default_factory=dict,
        description="Signals like trending mentions, press intensity, social heat",
    )
    sources: List[Dict[str, str]] = Field(
        default_factory=list, description="[{title, snippet, url}]"
    )


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

    # Market features (shared)
    market_features: Dict[str, Any]

    # Control / Debug
    errors: Annotated[List[str], operator.add]
