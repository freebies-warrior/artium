from __future__ import annotations

from path_bootstrap import ensure_src_on_path

ensure_src_on_path()

import agents.tasks.feature_extractor.service as feature_service


def test_build_initial_feature_state_uses_selected_primary_image(monkeypatch) -> None:
    calls: list[tuple[str, tuple[int, int]]] = []

    def fake_fetch(image_url: str, target_size: tuple[int, int]):
        calls.append((image_url, target_size))
        if target_size == (512, 512):
            return (f"thumb-{image_url}".encode(), "RGB", (512, 512))
        return (f"full-{image_url}".encode(), "RGB", (1024, 1024))

    monkeypatch.setattr(feature_service, "fetch_and_standardize_image", fake_fetch)
    monkeypatch.setattr(feature_service, "get_primary_image_index", lambda images: 1)

    initial_state, metadata, image_bytes = feature_service.build_initial_feature_state(
        image_urls=["img-1", "img-2"],
        item_id="item-123",
        metadata={"title": "Starry Night"},
    )

    assert calls == [
        ("img-1", (512, 512)),
        ("img-2", (512, 512)),
        ("img-2", (1024, 1024)),
    ]
    assert metadata["item_id"] == "item-123"
    assert metadata["title"] == "Starry Night"
    assert metadata["author"] == "Unknown"
    assert metadata["year"] == "Unknown"
    assert metadata["medium_hint"] == "Unknown"
    assert image_bytes == b"full-img-2"
    assert initial_state["image_bytes"] == b"full-img-2"
    assert initial_state["image_mode"] == "RGB"
    assert initial_state["image_size"] == (1024, 1024)
    assert initial_state["errors"] == []


def test_build_initial_feature_state_defaults_metadata_fields(monkeypatch) -> None:
    monkeypatch.setattr(
        feature_service,
        "fetch_and_standardize_image",
        lambda *_args, **_kwargs: (b"image-bytes", "RGB", (1024, 1024)),
    )
    monkeypatch.setattr(feature_service, "get_primary_image_index", lambda images: 0)

    _state, metadata, _image_bytes = feature_service.build_initial_feature_state(
        image_urls=["img-1"],
        item_id=None,
        metadata=None,
    )

    assert metadata["item_id"] == "None"
    assert metadata["title"] == "Unknown"
    assert metadata["author"] == "Unknown"
    assert metadata["year"] == "Unknown"
    assert metadata["medium_hint"] == "Unknown"
