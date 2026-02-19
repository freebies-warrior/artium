from __future__ import annotations

from pathlib import Path

import pytest

import agents.core.settings as core_settings


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    core_settings.get_settings.cache_clear()
    yield
    core_settings.get_settings.cache_clear()


def test_agents_root_points_to_agents_project() -> None:
    assert core_settings.AGENTS_ROOT.name == "agents"
    assert (core_settings.AGENTS_ROOT / "pyproject.toml").exists()


def test_env_file_points_to_agents_dotenv() -> None:
    assert core_settings.ENV_FILE == core_settings.AGENTS_ROOT / ".env"


def test_get_settings_uses_resolved_env_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "OPENAI_API_KEY=test-openai-key\nINTERNAL_TOKEN=test-internal-token\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("INTERNAL_TOKEN", raising=False)
    monkeypatch.setattr(core_settings, "ENV_FILE", env_file)
    core_settings.get_settings.cache_clear()

    settings = core_settings.get_settings()

    assert settings.OPENAI_API_KEY == "test-openai-key"
    assert settings.INTERNAL_TOKEN == "test-internal-token"
