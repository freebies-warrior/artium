from __future__ import annotations

from path_bootstrap import ensure_src_on_path

ensure_src_on_path()

from agents.core.types import ArtworkType, normalize_artwork_type
from agents.core.utils.errors import redacted_exc_info
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


def test_redacted_exc_info_redacts_message_and_keeps_traceback() -> None:
    try:
        raise ValueError("sensitive detail")
    except ValueError as exc:
        exc_type, redacted, traceback = redacted_exc_info(exc)

    assert exc_type is ValueError
    assert isinstance(redacted, ValueError)
    assert str(redacted) == ""
    assert traceback is not None


def test_redacted_exc_info_can_drop_traceback() -> None:
    try:
        raise RuntimeError("sensitive detail")
    except RuntimeError as exc:
        _, _, traceback = redacted_exc_info(exc, include_traceback=False)

    assert traceback is None
