from __future__ import annotations

from path_bootstrap import ensure_src_on_path

ensure_src_on_path()

import pandas as pd
import pytest

from agents.providers.rag.ingest.ingest_csv import _safe_meta


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("plain text", "plain text"),
        (7, 7),
        (3.5, 3.5),
        (float("nan"), None),
        (float("inf"), None),
        (-float("inf"), None),
        (pd.NA, None),
        (None, None),
    ],
)
def test_safe_meta_normalizes_missing_and_non_finite_values(value: object, expected: object) -> None:
    assert _safe_meta(value) == expected
