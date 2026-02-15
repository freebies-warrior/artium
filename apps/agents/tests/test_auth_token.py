from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app import require_internal_token
from core.settings import get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _create_test_app() -> FastAPI:
    app = FastAPI(dependencies=[Depends(require_internal_token)])

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def test_missing_internal_token_returns_500(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INTERNAL_TOKEN", "")
    with TestClient(_create_test_app(), raise_server_exceptions=False) as client:
        response = client.get("/health", headers={"X-Internal-Token": "anything"})

    assert response.status_code == 500
    assert response.json() == {"detail": "INTERNAL_TOKEN is not configured"}


def test_wrong_internal_token_returns_401(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INTERNAL_TOKEN", "expected-token")
    with TestClient(_create_test_app(), raise_server_exceptions=False) as client:
        response = client.get("/health", headers={"X-Internal-Token": "wrong-token"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid internal token"}


def test_correct_internal_token_returns_200(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INTERNAL_TOKEN", "expected-token")
    with TestClient(_create_test_app(), raise_server_exceptions=False) as client:
        response = client.get("/health", headers={"X-Internal-Token": "expected-token"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
