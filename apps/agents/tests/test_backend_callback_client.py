from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest
import requests

import agents.core.adapters.backend_callback_http as callback_http
from agents.core.adapters.backend_callback_http import HttpBackendCallbackClient
from agents.core.constants import (
    ITEM_FEATURES_CALLBACK_PATH_TEMPLATE,
    VISUALIZATION_CALLBACK_PATH_TEMPLATE,
)
from agents.core.types import JobStatus


def _stub_settings() -> SimpleNamespace:
    return SimpleNamespace(
        backend_url="https://backend.example",
        INTERNAL_TOKEN="internal-token",
    )


def test_update_visualization_logs_warning_with_sanitized_url(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    called: dict[str, object] = {}

    def fake_put_json(url: str, payload: dict, *, headers: dict, timeout: float):
        called["url"] = url
        called["payload"] = payload
        called["headers"] = headers
        called["timeout"] = timeout
        return SimpleNamespace(status_code=502)

    monkeypatch.setattr(callback_http, "get_settings", _stub_settings)
    monkeypatch.setattr(callback_http, "put_json", fake_put_json)
    caplog.set_level(logging.WARNING, logger="agents.core.adapters.backend_callback_http")

    client = HttpBackendCallbackClient()
    client.update_visualization(
        job_id="job-1?X-Amz-Signature=SECRET#frag",
        status=JobStatus.FAILED,
        result_description=None,
        error_message="boom",
    )

    record = next(
        (rec for rec in caplog.records if rec.getMessage() == "failed to update visualizer job"),
        None,
    )
    assert record is not None
    assert getattr(record, "task_name", None) == "backend_callback.update_visualization"
    assert getattr(record, "job_id", None) == "job-1?X-Amz-Signature=SECRET#frag"
    assert getattr(record, "status", None) == 502
    assert getattr(record, "url", None) == "https://backend.example/visualizations/job-1"
    assert "?" not in record.url
    assert "#" not in record.url
    assert called["url"] == (
        f"https://backend.example"
        f"{VISUALIZATION_CALLBACK_PATH_TEMPLATE.format(job_id='job-1?X-Amz-Signature=SECRET#frag')}"
    )
    assert called["payload"] == {
        "status": "failed",
        "result_description": None,
        "error_message": "boom",
    }
    assert called["headers"] == {"Authorization": "Bearer internal-token"}
    assert called["timeout"] == 10.0
    assert "X-Amz-Signature=SECRET" not in caplog.text
    assert "internal-token" not in caplog.text


def test_update_item_features_logs_warning_with_sanitized_url(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    called: dict[str, object] = {}

    def fake_put_json(url: str, payload: dict, *, headers: dict, timeout: float):
        called["url"] = url
        called["payload"] = payload
        called["headers"] = headers
        called["timeout"] = timeout
        return SimpleNamespace(status_code=503)

    monkeypatch.setattr(callback_http, "get_settings", _stub_settings)
    monkeypatch.setattr(callback_http, "put_json", fake_put_json)
    caplog.set_level(logging.WARNING, logger="agents.core.adapters.backend_callback_http")

    client = HttpBackendCallbackClient()
    client.update_item_features(
        item_id="item-789?X-Amz-Signature=SECRET#frag",
        feature_json={"key": "value"},
    )

    record = next(
        (
            rec
            for rec in caplog.records
            if rec.getMessage() == "failed to update feature extraction job"
        ),
        None,
    )
    assert record is not None
    assert getattr(record, "task_name", None) == "backend_callback.update_item_features"
    assert getattr(record, "item_id", None) == "item-789?X-Amz-Signature=SECRET#frag"
    assert getattr(record, "status", None) == 503
    assert getattr(record, "url", None) == "https://backend.example/items/item-789"
    assert "?" not in record.url
    assert "#" not in record.url
    assert called["url"] == (
        f"https://backend.example"
        f"{ITEM_FEATURES_CALLBACK_PATH_TEMPLATE.format(item_id='item-789?X-Amz-Signature=SECRET#frag')}"
    )
    assert called["payload"] == {"features": {"key": "value"}}
    assert called["headers"] == {"Authorization": "Bearer internal-token"}
    assert "X-Amz-Signature=SECRET" not in caplog.text


def test_update_item_features_logs_error_context_on_request_exception(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def raise_timeout(*args, **kwargs):
        raise requests.Timeout("request timed out X-Amz-Signature=SECRET")

    monkeypatch.setattr(callback_http, "get_settings", _stub_settings)
    monkeypatch.setattr(callback_http, "put_json", raise_timeout)
    caplog.set_level(logging.ERROR, logger="agents.core.adapters.backend_callback_http")

    client = HttpBackendCallbackClient()
    client.update_item_features(
        item_id="item-123?X-Amz-Signature=SECRET#frag",
        feature_json={"key": "value"},
    )

    record = next(
        (
            rec
            for rec in caplog.records
            if rec.getMessage() == "failed to send feature extraction job update"
        ),
        None,
    )
    assert record is not None
    assert getattr(record, "task_name", None) == "backend_callback.update_item_features"
    assert getattr(record, "item_id", None) == "item-123?X-Amz-Signature=SECRET#frag"
    assert getattr(record, "error_type", None) == "Timeout"
    assert getattr(record, "url", None) == "https://backend.example/items/item-123"
    assert "?" not in record.url
    assert "#" not in record.url
    assert "X-Amz-Signature=SECRET" not in caplog.text
    assert "internal-token" not in caplog.text
