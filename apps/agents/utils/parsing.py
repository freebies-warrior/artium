from __future__ import annotations

import json
from typing import Any


def normalize_json_response_text(text: str | None) -> str:
    normalized = (text or "").strip()
    return normalized.removeprefix("```json").removeprefix("```").split("```")[0].strip()


def parse_json_object(text: str | None, *, source: str) -> dict[str, Any]:
    normalized = normalize_json_response_text(text)
    if not normalized:
        raise ValueError(f"{source}: expected JSON object response but received empty content")

    try:
        parsed = json.loads(normalized)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{source}: expected JSON object response; failed to parse JSON at "
            f"line {exc.lineno}, column {exc.colno}"
        ) from exc

    if not isinstance(parsed, dict):
        raise ValueError(f"{source}: expected JSON object response but got {type(parsed).__name__}")

    return parsed
