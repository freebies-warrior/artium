from __future__ import annotations

from pathlib import Path


def _resolve_api_agent_path() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "agents" / "api" / "agent.py"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Unable to locate agents/api/agent.py from test path")


def test_api_agent_module_does_not_import_visualizer_private_internals() -> None:
    api_agent_path = _resolve_api_agent_path()
    source = api_agent_path.read_text(encoding="utf-8")

    assert (
        "from agents.tasks.visualizer.classify_node import is_valid_artwork_and_room" not in source
    )
    assert "from agents.tasks.visualizer.pipeline_langgraph import VizState" not in source
    assert "from agents.tasks.visualizer.pipeline_sequential import _load_image" not in source
    assert "from agents.tasks.visualizer.runner import _save_image" not in source

    assert "from agents.tasks.visualizer.service import load_preview_images" not in source
    assert "service.run_preview_job(command)" in source
