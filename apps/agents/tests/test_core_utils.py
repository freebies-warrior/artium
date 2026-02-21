from __future__ import annotations

from agents.core.types import ArtworkType, normalize_artwork_type
from agents.core.utils.files import sanitize_output_filename
from agents.core.utils.http import internal_auth_headers


def test_sanitize_output_filename_applies_default_suffix() -> None:
    assert sanitize_output_filename("preview") == "preview.jpeg"


def test_internal_auth_headers_strips_token() -> None:
    assert internal_auth_headers("  secret-token  ") == {"Authorization": "Bearer secret-token"}


def test_normalize_artwork_type_maps_not_artwork_aliases() -> None:
    assert normalize_artwork_type("NOT AN ARTWORK") == ArtworkType.NOT_ARTWORK.value
    assert normalize_artwork_type("not_artwork") == ArtworkType.NOT_ARTWORK.value
    assert normalize_artwork_type("not-artwork") == ArtworkType.NOT_ARTWORK.value


def test_normalize_artwork_type_keeps_supported_types() -> None:
    assert normalize_artwork_type("painting") == ArtworkType.PAINTING.value
    assert normalize_artwork_type("sculpture") == ArtworkType.SCULPTURE.value
