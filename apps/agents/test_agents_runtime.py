from __future__ import annotations

import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

AGENTS_ROOT = Path(__file__).resolve().parent
if str(AGENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENTS_ROOT))

import app as agents_app
from api import agent as agent_api
from api import service as service_api


def _patch_service_builders(monkeypatch, seen: list[tuple[str, str | None]]) -> None:
    class FakeVisionClient:
        def __init__(self, api_key: str | None = None):
            seen.append(("vision", api_key))

    class FakeClient:
        def __init__(self, api_key: str | None = None):
            seen.append(("visualizer", api_key))

    monkeypatch.setattr(service_api, "GeminiVisionClient", FakeVisionClient)
    monkeypatch.setattr(service_api, "GeminiClient", FakeClient)
    monkeypatch.setattr(service_api, "build_graph", lambda vision_llm: "graph")
    monkeypatch.setattr(service_api, "build_visualization_graph", lambda: "viz")
    monkeypatch.setattr(service_api, "build_valuation_graph", lambda: "valuation")


@pytest.mark.parametrize("token", [None, "", "   "])
def test_agent_service_startup_rejects_missing_internal_token(
    monkeypatch, token: str | None
) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    if token is None:
        monkeypatch.delenv("INTERNAL_TOKEN", raising=False)
    else:
        monkeypatch.setenv("INTERNAL_TOKEN", token)

    seen: list[tuple[str, str | None]] = []
    _patch_service_builders(monkeypatch, seen)

    with pytest.raises(RuntimeError, match="INTERNAL_TOKEN is required"):
        service_api.AgentService().initialize()


def test_agent_service_initialize_strips_and_stores_internal_token(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("INTERNAL_TOKEN", "  secret-token  ")

    seen: list[tuple[str, str | None]] = []
    _patch_service_builders(monkeypatch, seen)

    service = service_api.AgentService()
    service.initialize()

    assert service.internal_token == "secret-token"
    assert seen == [("vision", "google-key"), ("visualizer", "google-key")]


def test_require_internal_token_uses_service_token(monkeypatch) -> None:
    monkeypatch.setattr(
        agents_app,
        "get_agent_service",
        lambda: SimpleNamespace(internal_token="secret-token"),
    )

    agents_app.require_internal_token("secret-token")

    with pytest.raises(HTTPException, match="Invalid internal token"):
        agents_app.require_internal_token("wrong")


@pytest.mark.parametrize(
    ("call", "path"),
    [
        (
            lambda: agent_api._notify_backend_preview(
                "job-1",
                agent_api.JobStatus.SUCCEEDED,
                "done",
                None,
                "secret-token",
            ),
            "/visualizations/job-1",
        ),
        (
            lambda: agent_api._notify_backend_feature_extraction(
                uuid.UUID(int=1),
                {"foo": "bar"},
                "secret-token",
            ),
            f"/items/{uuid.UUID(int=1)}/features",
        ),
    ],
)
def test_notify_backends_always_attach_internal_token(
    monkeypatch, call, path: str
) -> None:
    captured: dict[str, object] = {}

    class Response:
        status_code = 200

    def fake_put(url, json=None, headers=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(agent_api, "BACKEND_URL", "http://backend.test")
    monkeypatch.setattr(agent_api.requests, "put", fake_put)

    call()

    assert captured["url"] == f"http://backend.test{path}"
    assert captured["headers"] == {"Authorization": "Bearer secret-token"}
