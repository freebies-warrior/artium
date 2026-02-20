from __future__ import annotations

from pathlib import Path


def test_api_agent_module_uses_feature_extractor_service_boundary() -> None:
    api_agent_path = Path(__file__).resolve().parents[1] / "agents" / "api" / "agent.py"
    source = api_agent_path.read_text(encoding="utf-8")

    assert (
        "from agents.tasks.feature_extractor.single_select import get_primary_image_index"
        not in source
    )
    assert (
        "from agents.tasks.feature_extractor.tools.image_tool import fetch_and_standardize_image"
        not in source
    )
    assert (
        "from agents.tasks.feature_extractor.service import build_initial_feature_state" in source
    )
