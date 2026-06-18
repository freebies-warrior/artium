from path_bootstrap import ensure_src_on_path

ensure_src_on_path()

from agents.core.utils.json import sanitize_for_json


def test_sanitize_for_json_removes_binary_values() -> None:
    payload = {
        "keep": "value",
        "drop_bytes": b"x",
        "nested": {"keep_nested": 1, "drop_nested": bytearray(b"y")},
        "items": [1, b"z", {"drop_too": b"k", "keep_too": "ok"}],
        "coords": (10, 20),
    }

    assert sanitize_for_json(payload) == {
        "keep": "value",
        "nested": {"keep_nested": 1},
        "items": [1, {"keep_too": "ok"}],
        "coords": [10, 20],
    }


def test_sanitize_for_json_returns_none_for_top_level_bytes() -> None:
    assert sanitize_for_json(b"raw-binary") is None
