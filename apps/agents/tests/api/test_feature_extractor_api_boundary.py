from __future__ import annotations

from pathlib import Path


def _resolve_api_agent_path() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "src" / "agents" / "api" / "agent.py"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Unable to locate src/agents/api/agent.py from test path")


def test_api_agent_module_uses_feature_extractor_service_boundary() -> None:
    api_agent_path = _resolve_api_agent_path()
    source = api_agent_path.read_text(encoding="utf-8")

    assert (
        "from agents.tasks.feature_extractor.single_select import get_primary_image_index"
        not in source
    )
    assert (
        "from agents.tasks.feature_extractor.tools.image_tool import fetch_and_standardize_image"
        not in source
    )
    assert "build_initial_feature_state" not in source
    assert "service.run_feature_extraction_job(command)" in source
