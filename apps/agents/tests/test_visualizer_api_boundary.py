from __future__ import annotations

from pathlib import Path


def test_api_agent_module_does_not_import_visualizer_private_internals() -> None:
    api_agent_path = Path(__file__).resolve().parents[1] / "agents" / "api" / "agent.py"
    source = api_agent_path.read_text(encoding="utf-8")

    assert (
        "from agents.tasks.visualizer.classify_node import is_valid_artwork_and_room" not in source
    )
    assert "from agents.tasks.visualizer.pipeline_langgraph import VizState" not in source
    assert "from agents.tasks.visualizer.pipeline_sequential import _load_image" not in source
    assert "from agents.tasks.visualizer.runner import _save_image" not in source

    assert "from agents.tasks.visualizer.service import load_preview_images" not in source
    assert "service.run_preview_job(command)" in source
