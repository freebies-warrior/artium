from __future__ import annotations

from typing import Any

import requests


def internal_auth_headers(token: str | None) -> dict[str, str]:
    token_value = (token or "").strip()
    if not token_value:
        return {}
    return {"Authorization": f"Bearer {token_value}"}


def put_json(
    url: str,
    payload: dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 10.0,
) -> requests.Response:
    return requests.put(url, json=payload, headers=headers or {}, timeout=timeout)


def put_bytes(
    url: str,
    data: bytes,
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> requests.Response:
    return requests.put(url, data=data, headers=headers or {}, timeout=timeout)
