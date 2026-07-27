from uuid import uuid4

import pytest
from pydantic import ValidationError

from path_bootstrap import ensure_src_on_path

ensure_src_on_path()

from agents.api.agent import FeatureExtractionRequest, VisualizerRequest


def test_feature_extraction_request_metadata_uses_default_factory() -> None:
    metadata_field = FeatureExtractionRequest.model_fields["metadata"]
    assert metadata_field.default_factory is dict


def test_feature_extraction_request_metadata_is_not_shared_between_instances() -> None:
    first = FeatureExtractionRequest(
        item_id=uuid4(),
        image_keys=["one"],
        image_get_urls=["https://example.com/one.jpg"],
    )
    second = FeatureExtractionRequest(
        item_id=uuid4(),
        image_keys=["two"],
        image_get_urls=["https://example.com/two.jpg"],
    )

    first.metadata["source"] = "first"

    assert first.metadata == {"source": "first"}
    assert second.metadata == {}


def test_visualizer_request_accepts_go_client_contract_payload() -> None:
    request = VisualizerRequest.model_validate(
        {
            "room_url": "https://example.com/room.jpg",
            "art_url": "https://example.com/art.jpg",
            "upload_image_url": "https://example.com/upload.jpg",
            "result_image_key": "visualizations/job-123/result.jpg",
            "item_dimensions": {"width": 60.5, "height": 40.25},
            "job_id": "job-123",
        }
    )

    assert request.result_image_key == "visualizations/job-123/result.jpg"
    assert request.item_dimensions is not None
    assert request.item_dimensions.width == 60.5
    assert request.item_dimensions.height == 40.25


def test_visualizer_request_rejects_legacy_upload_image_key_field() -> None:
    with pytest.raises(ValidationError):
        VisualizerRequest.model_validate(
            {
                "room_url": "https://example.com/room.jpg",
                "art_url": "https://example.com/art.jpg",
                "upload_image_url": "https://example.com/upload.jpg",
                "upload_image_key": "visualizations/job-123/result.jpg",
                "item_dimensions": {"width": 60.5, "height": 40.25},
                "job_id": "job-123",
            }
        )
