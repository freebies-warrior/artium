from __future__ import annotations

from pathlib import Path

import pytest

from agents.core.settings import get_settings
from agents.providers.rag.settings import load_config


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _write_config(path: Path, embedding_mode: str = "feature_text") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"embedding_mode: {embedding_mode}\n", encoding="utf-8")


def test_load_config_uses_explicit_path_without_fallback(tmp_path: Path) -> None:
    explicit = tmp_path / "explicit.yaml"
    _write_config(explicit, embedding_mode="numeric")

    cfg = load_config(explicit)

    assert cfg.path == explicit
    assert cfg.embedding_mode == "numeric"


def test_load_config_prefers_new_default_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    new_path = tmp_path / "agents/providers/rag/config.yaml"
    _write_config(new_path, embedding_mode="feature_text")

    cfg = load_config()

    assert cfg.path == Path("agents/providers/rag/config.yaml")
    assert cfg.embedding_mode == "feature_text"


def test_load_config_falls_back_to_legacy_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    legacy_path = tmp_path / "RAG/config.yaml"
    _write_config(legacy_path, embedding_mode="image")

    cfg = load_config()

    assert cfg.path == Path("RAG/config.yaml")
    assert cfg.embedding_mode == "image"


def test_load_config_raises_when_no_default_path_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(FileNotFoundError) as exc:
        load_config()

    message = str(exc.value)
    assert "agents/providers/rag/config.yaml" in message
    assert "RAG/config.yaml" in message
