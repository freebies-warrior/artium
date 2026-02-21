from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from agents.api.agent import FeatureExtractionRequest


def test_feature_extraction_request_requires_item_id() -> None:
    with pytest.raises(ValidationError) as exc:
        FeatureExtractionRequest(
            image_keys=["img1"],
            image_get_urls=["https://example.com/images/1.jpg"],
        )

    assert "item_id" in str(exc.value)
    assert "Field required" in str(exc.value)


def test_feature_extraction_request_rejects_empty_image_keys() -> None:
    with pytest.raises(ValidationError) as exc:
        FeatureExtractionRequest(
            item_id=uuid4(),
            image_keys=[],
            image_get_urls=["https://example.com/images/1.jpg"],
        )

    assert "image_keys" in str(exc.value)
    assert "at least 1 item" in str(exc.value)


def test_feature_extraction_request_rejects_empty_image_get_urls() -> None:
    with pytest.raises(ValidationError) as exc:
        FeatureExtractionRequest(
            item_id=uuid4(),
            image_keys=["img1"],
            image_get_urls=[],
        )

    assert "image_get_urls" in str(exc.value)
    assert "at least 1 item" in str(exc.value)


def test_feature_extraction_request_rejects_mismatched_image_list_lengths() -> None:
    with pytest.raises(ValidationError) as exc:
        FeatureExtractionRequest(
            item_id=uuid4(),
            image_keys=["img1", "img2"],
            image_get_urls=["https://example.com/images/1.jpg"],
        )

    assert "image_keys and image_get_urls must have the same length" in str(exc.value)


def test_feature_extraction_request_accepts_valid_payload() -> None:
    req = FeatureExtractionRequest(
        item_id=uuid4(),
        image_keys=["img1"],
        image_get_urls=["https://example.com/images/1.jpg"],
    )

    assert req.item_id is not None
    assert req.image_keys == ["img1"]
    assert [str(url) for url in req.image_get_urls] == ["https://example.com/images/1.jpg"]
