from uuid import uuid4

from path_bootstrap import ensure_src_on_path

ensure_src_on_path()

from agents.api.agent import FeatureExtractionRequest


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
