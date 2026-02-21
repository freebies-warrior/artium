from __future__ import annotations

from agents.tasks.feature_extractor import prompt


def test_feature_extractor_prompts_require_json_only_response() -> None:
    metadata = {"title": "Untitled", "author": "Unknown", "year": 1999}
    builders = [
        prompt.build_brushstroke_prompt,
        prompt.build_blending_prompt,
        prompt.build_physicality_prompt,
        prompt.build_material_prompt,
        prompt.build_form_prompt,
        prompt.build_surface_prompt,
        prompt.build_craftsmanship_prompt,
    ]

    for build_prompt in builders:
        text = build_prompt(metadata)
        assert text
        assert "Return ONLY valid JSON" in text
        assert '"title": "Untitled"' in text
