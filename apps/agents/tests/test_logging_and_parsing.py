from __future__ import annotations

import logging

import pytest
import requests

import core.logging as core_logging
from core.utils.http import loggable_url
from core.utils.http import put_json
from core.utils.parsing import parse_json_object


def test_loggable_url_strips_query_and_fragment() -> None:
    url = "https://example.com/path/file.jpg?X-Amz-Signature=SECRET#frag"
    assert loggable_url(url) == "https://example.com/path/file.jpg"


def test_parse_json_object_invalid_output_has_actionable_message() -> None:
    with pytest.raises(ValueError) as exc:
        parse_json_object("{not-valid-json}", source="feature_extractor.generate_json")

    message = str(exc.value)
    assert "feature_extractor.generate_json" in message
    assert "expected JSON object response" in message
    assert "line" in message and "column" in message


def test_put_json_timeout_logs_actionable_context(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def raise_timeout(*args, **kwargs):
        raise requests.Timeout(
            "timed out while calling https://example.com/api/resource?token=secret"
        )

    monkeypatch.setattr("core.utils.http.requests.put", raise_timeout)
    caplog.set_level(logging.ERROR, logger="core.utils.http")

    with pytest.raises(requests.Timeout):
        put_json("https://example.com/api/resource?token=secret", {"ok": True}, timeout=1.5)

    record = next(
        (rec for rec in caplog.records if rec.getMessage() == "http request failed"), None
    )
    assert record is not None
    assert getattr(record, "method", None) == "PUT"
    assert getattr(record, "url", None) == "https://example.com/api/resource"
    assert getattr(record, "timeout", None) == 1.5
    assert getattr(record, "error_type", None) == "Timeout"
    assert "token=secret" not in caplog.text


def test_configure_logging_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(core_logging, "_configured_level", None)

    core_logging.configure_logging("INFO")
    first_handlers = tuple(id(handler) for handler in logging.getLogger().handlers)
    core_logging.configure_logging("INFO")
    second_handlers = tuple(id(handler) for handler in logging.getLogger().handlers)

    assert first_handlers == second_handlers
