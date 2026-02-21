from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

import agents.api.agent as agent_api
from app import require_internal_token
from agents.core.settings import get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _create_test_app() -> FastAPI:
    app = FastAPI(dependencies=[Depends(require_internal_token)])
    app.include_router(agent_api.feature_extractor_router)
    return app


def _headers() -> dict[str, str]:
    return {"X-Internal-Token": "expected-token"}


def test_extract_endpoint_rejects_missing_item_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INTERNAL_TOKEN", "expected-token")
    payload = {
        "image_keys": ["img1"],
        "image_get_urls": ["https://example.com/images/1.jpg"],
    }
    with TestClient(_create_test_app(), raise_server_exceptions=False) as client:
        response = client.post(
            "/agents/feature_extractor/extract",
            json=payload,
            headers=_headers(),
        )

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(error["loc"][-1] == "item_id" for error in errors)


def test_extract_endpoint_rejects_empty_image_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INTERNAL_TOKEN", "expected-token")
    payload = {
        "item_id": str(uuid4()),
        "image_keys": [],
        "image_get_urls": ["https://example.com/images/1.jpg"],
    }
    with TestClient(_create_test_app(), raise_server_exceptions=False) as client:
        response = client.post(
            "/agents/feature_extractor/extract",
            json=payload,
            headers=_headers(),
        )

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(error["loc"][-1] == "image_keys" for error in errors)


def test_extract_endpoint_rejects_mismatched_image_lists(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INTERNAL_TOKEN", "expected-token")
    payload = {
        "item_id": str(uuid4()),
        "image_keys": ["img1", "img2"],
        "image_get_urls": ["https://example.com/images/1.jpg"],
    }
    with TestClient(_create_test_app(), raise_server_exceptions=False) as client:
        response = client.post(
            "/agents/feature_extractor/extract",
            json=payload,
            headers=_headers(),
        )

    assert response.status_code == 422
    assert "image_keys and image_get_urls must have the same length" in response.text


def test_extract_endpoint_accepts_valid_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INTERNAL_TOKEN", "expected-token")
    monkeypatch.setattr(agent_api, "_extract_features", lambda req: None)

    payload = {
        "item_id": str(uuid4()),
        "image_keys": ["img1"],
        "image_get_urls": ["https://example.com/images/1.jpg"],
    }
    with TestClient(_create_test_app(), raise_server_exceptions=False) as client:
        response = client.post(
            "/agents/feature_extractor/extract",
            json=payload,
            headers=_headers(),
        )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
