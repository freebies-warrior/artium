from __future__ import annotations

from core.utils.files import sanitize_output_filename
from core.utils.http import internal_auth_headers


def test_sanitize_output_filename_applies_default_suffix() -> None:
    assert sanitize_output_filename("preview") == "preview.jpeg"


def test_internal_auth_headers_strips_token() -> None:
    assert internal_auth_headers("  secret-token  ") == {"Authorization": "Bearer secret-token"}
