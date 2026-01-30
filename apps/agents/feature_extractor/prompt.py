from __future__ import annotations

import json
from typing import Any, Dict

from .types import (
    BrushstrokeDynamics,
    BlendingMerging,
    Physicality,
    MaterialComposition,
    Form,
    SurfaceFinish,
    Craftsmanship,
)


def build_brushstroke_prompt(metadata: Dict[str, Any]) -> str:
    return f"""
You are a senior Sotheby's specialist. Extract brushstroke dynamics that affect price.
Return ONLY valid JSON that matches this schema:

{BrushstrokeDynamics.model_json_schema()}

Artwork metadata:
{json.dumps(metadata, indent=2)}

Guidelines:
- Use probabilities in [0,1] for impasto/glazing/stippling.
- Ground your reasoning in visible cues (edges, texture, paint thickness, translucency).
- If unsure, lower confidence and explain why in notes.
""".strip()


def build_blending_prompt(metadata: Dict[str, Any]) -> str:
    return f"""
You are a senior Sotheby's specialist. Extract blending/edge behavior that affects price.
Return ONLY valid JSON that matches this schema:

{BlendingMerging.model_json_schema()}

Artwork metadata:
{json.dumps(metadata, indent=2)}

Guidelines:
- Use probabilities in [0,1] for sfumato/hard_edge.
- Focus on transitions, boundary softness, and edge clarity.
- If unsure, lower confidence and explain why in notes.
""".strip()


def build_physicality_prompt(metadata: Dict[str, Any]) -> str:
    return f"""
You are a senior Sotheby's specialist. Extract medium/support/texture that affects price.
Return ONLY valid JSON that matches this schema:

{Physicality.model_json_schema()}

Artwork metadata:
{json.dumps(metadata, indent=2)}

Guidelines:
- Be concise and stick to visible cues (sheen, weave, grain, translucency).
- If unsure, state uncertainty in notes.
""".strip()


def build_material_prompt(metadata: Dict[str, Any]) -> str:
    return f"""
You are a senior Christie's sculpture specialist. Extract material composition that affects price.
Return ONLY valid JSON that matches this schema:

{MaterialComposition.model_json_schema()}

Artwork metadata:
{json.dumps(metadata, indent=2)}

Guidelines:
- Identify primary and secondary materials from visual inspection (marble, bronze, stone, wood, etc.).
- Use material_confidence in [0,1] based on visual cues and patina.
- If unsure, lower confidence and explain why in notes.
""".strip()


def build_form_prompt(metadata: Dict[str, Any]) -> str:
    return f"""
You are a senior Christie's sculpture specialist. Extract form and composition that affects price.
Return ONLY valid JSON that matches this schema:

{Form.model_json_schema()}

Artwork metadata:
{json.dumps(metadata, indent=2)}

Guidelines:
- Describe overall visual form, balance, symmetry, and proportions.
- Use composition_balance in [0,1] to assess visual equilibrium.
- Focus on compositional principles and visual harmony.
""".strip()


def build_surface_prompt(metadata: Dict[str, Any]) -> str:
    return f"""
You are a senior Christie's sculpture specialist. Extract surface finish quality that affects price.
Return ONLY valid JSON that matches this schema:

{SurfaceFinish.model_json_schema()}

Artwork metadata:
{json.dumps(metadata, indent=2)}

Guidelines:
- Identify surface type (polished, matte, weathered, patinated, etc.).
- Use surface_quality in [0,1] to assess finish quality and condition.
- Document any visible damage, weathering, repairs, or patina.
""".strip()


def build_craftsmanship_prompt(metadata: Dict[str, Any]) -> str:
    return f"""
You are a senior Christie's sculpture specialist. Extract craftsmanship quality that affects price.
Return ONLY valid JSON that matches this schema:

{Craftsmanship.model_json_schema()}

Artwork metadata:
{json.dumps(metadata, indent=2)}

Guidelines:
- Assess detail level, precision, carving technique, or casting quality.
- Use quality_assessment in [0,1] to rate overall execution quality.
- Identify visible techniques (chisel marks, casting seams, finishing methods, etc.).
""".strip()
