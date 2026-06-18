from __future__ import annotations

from typing import Any


def sanitize_for_json(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray)):
        return None
    if isinstance(value, dict):
        return {
            key: sanitize_for_json(val)
            for key, val in value.items()
            if not isinstance(val, (bytes, bytearray))
        }
    if isinstance(value, list):
        return [
            sanitize_for_json(item) for item in value if not isinstance(item, (bytes, bytearray))
        ]
    if isinstance(value, tuple):
        return [sanitize_for_json(item) for item in value]
    return value
