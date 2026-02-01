from __future__ import annotations

import re
from typing import Any, Dict, Tuple


_URL_RE = re.compile(r"https?://\S+")


def _strip_urls(text: str) -> str:
    return _URL_RE.sub("", text).strip()


def _cap(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    text = text.strip()
    return text if len(text) <= max_chars else text[: max_chars - 1].rstrip() + "…"


def preprocess_notes(
    notes: str,
    *,
    strip_urls: bool = True,
    max_chars: int = 250,
) -> str:
    if not notes:
        return ""
    s = str(notes)
    if strip_urls:
        s = _strip_urls(s)
    s = re.sub(r"\s+", " ", s).strip()
    return _cap(s, max_chars)


def canonicalize_painting(
    vision_features: Dict[str, Any],
    *,
    strip_urls: bool,
    max_chars_per_section: int,
) -> Dict[str, Any]:
    brush = vision_features.get("brushstroke", {}) or {}
    blend = vision_features.get("blending", {}) or {}
    phys = vision_features.get("physicality", {}) or {}

    return {
        "type": "painting",
        "medium_detected": phys.get("medium_detected") or phys.get("medium") or "",
        "support_detected": phys.get("support_detected") or phys.get("support") or "",
        "signals": {
            "impasto": brush.get("impasto", 0.0),
            "glazing": brush.get("glazing", 0.0),
            "stippling": brush.get("stippling", 0.0),
            "sfumato": blend.get("sfumato", 0.0),
            "hard_edge": blend.get("hard_edge", 0.0),
        },
        "notes": {
            "brushstroke": preprocess_notes(
                brush.get("notes", ""), strip_urls=strip_urls, max_chars=max_chars_per_section
            ),
            "blending": preprocess_notes(
                blend.get("notes", ""), strip_urls=strip_urls, max_chars=max_chars_per_section
            ),
            "physicality": preprocess_notes(
                phys.get("notes", ""), strip_urls=strip_urls, max_chars=max_chars_per_section
            ),
            "justification": preprocess_notes(
                vision_features.get("justification", ""),
                strip_urls=strip_urls,
                max_chars=max_chars_per_section,
            ),
        },
    }


def canonicalize_sculpture(
    vision_features: Dict[str, Any],
    *,
    strip_urls: bool,
    max_chars_per_section: int,
) -> Dict[str, Any]:
    material = vision_features.get("material", {}) or {}
    form = vision_features.get("form", {}) or {}
    surface = vision_features.get("surface", {}) or {}
    craft = vision_features.get("craftsmanship", {}) or {}

    return {
        "type": "sculpture",
        "signals": {
            # Fill these with whatever numeric fields your extractor emits.
            # Missing keys -> 0.0
            "metal": material.get("metal", 0.0),
            "wood": material.get("wood", 0.0),
            "angularity": form.get("angularity", 0.0),
            "polish": surface.get("polish", 0.0),
            "craftsmanship": craft.get("score", craft.get("craftsmanship", 0.0)),
        },
        "notes": {
            "material": preprocess_notes(
                material.get("notes", ""), strip_urls=strip_urls, max_chars=max_chars_per_section
            ),
            "form": preprocess_notes(
                form.get("notes", ""), strip_urls=strip_urls, max_chars=max_chars_per_section
            ),
            "surface": preprocess_notes(
                surface.get("notes", ""), strip_urls=strip_urls, max_chars=max_chars_per_section
            ),
            "craftsmanship": preprocess_notes(
                craft.get("notes", ""), strip_urls=strip_urls, max_chars=max_chars_per_section
            ),
            "justification": preprocess_notes(
                vision_features.get("justification", ""),
                strip_urls=strip_urls,
                max_chars=max_chars_per_section,
            ),
        },
    }


def canonicalize_feature_state(
    feature_state: Dict[str, Any],
    *,
    strip_urls: bool = True,
    max_chars_total: int = 800,
    max_chars_per_section: int = 250,
    schema_version: str = "v1",
) -> Tuple[str, Dict[str, Any]]:
    artwork_type = (feature_state.get("artwork_type") or "").lower().strip()
    vision_features = feature_state.get("vision_features") or {}

    if artwork_type == "painting":
        canon = canonicalize_painting(
            vision_features, strip_urls=strip_urls, max_chars_per_section=max_chars_per_section
        )
    elif artwork_type == "sculpture":
        canon = canonicalize_sculpture(
            vision_features, strip_urls=strip_urls, max_chars_per_section=max_chars_per_section
        )
    else:
        raise ValueError(f"Unsupported artwork_type={artwork_type!r}")

    canon["schema_version"] = schema_version

    # Deterministic text serialization (stable order)
    lines = []
    lines.append(f"type: {canon.get('type','')}")
    if canon.get("type") == "painting":
        lines.append(f"medium: {canon.get('medium_detected','')}")
        lines.append(f"support: {canon.get('support_detected','')}")
    signals = canon.get("signals", {}) or {}
    for k in sorted(signals.keys()):
        lines.append(f"{k}: {signals.get(k, 0.0)}")
    notes = canon.get("notes", {}) or {}
    for k in sorted(notes.keys()):
        v = notes.get(k, "")
        if v:
            lines.append(f"note_{k}: {v}")

    text = "\n".join(lines).strip()
    text = _cap(text, max_chars_total)
    return text, canon
