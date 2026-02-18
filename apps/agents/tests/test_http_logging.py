from __future__ import annotations

import logging

import pytest
import requests

from agents.core.utils.http import loggable_url, put_json


def test_loggable_url_strips_query_and_fragment() -> None:
    url = "https://example.com/path/file.jpg?X-Amz-Signature=SECRET#frag"
    assert loggable_url(url) == "https://example.com/path/file.jpg"


def test_put_json_timeout_logs_actionable_sanitized_context(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    signed_url = "https://example.com/api/resource?X-Amz-Signature=SECRET#frag"

    def raise_timeout(*args, **kwargs):
        raise requests.Timeout(f"timed out while calling {signed_url}")

    monkeypatch.setattr("agents.core.utils.http.requests.put", raise_timeout)
    caplog.set_level(logging.ERROR, logger="agents.core.utils.http")

    with pytest.raises(requests.Timeout):
        put_json(signed_url, {"ok": True}, timeout=1.5)

    record = next(
        (rec for rec in caplog.records if rec.getMessage() == "http request failed"),
        None,
    )
    assert record is not None
    assert getattr(record, "method", None) == "PUT"
    assert getattr(record, "url", None) == "https://example.com/api/resource"
    assert getattr(record, "timeout", None) == 1.5
    assert getattr(record, "error_type", None) == "Timeout"
    assert "?" not in record.url
    assert "#" not in record.url
    assert "X-Amz-Signature=SECRET" not in caplog.text
