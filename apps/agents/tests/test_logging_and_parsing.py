from __future__ import annotations

import logging

import pytest
import requests

from core.utils.http import put_json
from core.utils.parsing import parse_json_object


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
        raise requests.Timeout("timed out")

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
