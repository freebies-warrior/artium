import agents.tasks.visualizer.runner as migrated
from agents.api import agent as api_agent


def test_visualizer_runner_import_smoke() -> None:
    assert callable(migrated.visualize_installation)


def test_api_agent_import_smoke() -> None:
    assert api_agent.visualizer_router is not None
