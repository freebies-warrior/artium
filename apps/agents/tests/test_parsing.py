from __future__ import annotations

import pytest

from core.utils.parsing import parse_json_object


def test_parse_json_object_rejects_empty_content() -> None:
    with pytest.raises(ValueError) as exc:
        parse_json_object("   ", source="feature_extractor.generate_json")

    message = str(exc.value)
    assert "feature_extractor.generate_json" in message
    assert "empty content" in message


def test_parse_json_object_rejects_invalid_json_with_location() -> None:
    with pytest.raises(ValueError) as exc:
        parse_json_object("{not-valid-json}", source="feature_extractor.generate_json")

    message = str(exc.value)
    assert "feature_extractor.generate_json" in message
    assert "line" in message
    assert "column" in message


@pytest.mark.parametrize(
    ("payload", "expected_type"),
    [
        ("[]", "list"),
        ('"text"', "str"),
    ],
)
def test_parse_json_object_rejects_non_object_json(payload: str, expected_type: str) -> None:
    with pytest.raises(ValueError) as exc:
        parse_json_object(payload, source="feature_extractor.generate_json")

    message = str(exc.value)
    assert "expected JSON object" in message
    assert expected_type in message
