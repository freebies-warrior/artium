from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .single_select import get_primary_image_index
from .tools.image_tool import fetch_and_standardize_image
from .types import ArtworkMetadata, FeatureState


def build_initial_feature_state(
    *,
    image_urls: Sequence[str],
    item_id: str | None,
    metadata: Mapping[str, Any] | None = None,
) -> tuple[FeatureState, dict[str, Any], bytes]:
    request_metadata = metadata or {}

    selected_index = get_primary_image_index(
        images=[
            fetch_and_standardize_image(image_url, target_size=(512, 512))[0]
            for image_url in image_urls
        ]
    )
    image_url = image_urls[selected_index]

    metadata_dict = ArtworkMetadata(
        item_id=str(item_id),
        title=request_metadata.get("title", "Unknown"),
        author=request_metadata.get("author", "Unknown"),
        year=str(request_metadata.get("year", "Unknown")),
        medium_hint=request_metadata.get("medium_hint", "Unknown"),
    ).model_dump()

    image_bytes, image_mode, image_size = fetch_and_standardize_image(
        image_url, target_size=(1024, 1024)
    )

    initial_state: FeatureState = {
        "metadata": metadata_dict,
        "image_bytes": image_bytes,
        "image_mode": image_mode,
        "image_size": image_size,
        "errors": [],
    }

    return initial_state, metadata_dict, image_bytes
