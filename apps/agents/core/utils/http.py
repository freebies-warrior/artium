from __future__ import annotations

import logging
from types import TracebackType
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import requests

logger = logging.getLogger(__name__)


def _redacted_exc_info(
    exc: BaseException,
) -> tuple[type[BaseException], BaseException, TracebackType | None]:
    """Preserve traceback while redacting potentially sensitive exception text."""
    try:
        redacted = type(exc)()
    except Exception:
        redacted = Exception(type(exc).__name__)
    return type(exc), redacted, exc.__traceback__


def loggable_url(url: str) -> str:
    parsed = urlsplit(url)
    # Drop query/fragment to avoid leaking signed URL parameters.
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


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
    try:
        return requests.put(url, json=payload, headers=headers or {}, timeout=timeout)
    except requests.RequestException as exc:
        logger.exception(
            "http request failed",
            extra={
                "method": "PUT",
                "url": loggable_url(url),
                "timeout": timeout,
                "error_type": type(exc).__name__,
            },
            exc_info=_redacted_exc_info(exc),
        )
        raise


def put_bytes(
    url: str,
    data: bytes,
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> requests.Response:
    try:
        return requests.put(url, data=data, headers=headers or {}, timeout=timeout)
    except requests.RequestException as exc:
        logger.exception(
            "http request failed",
            extra={
                "method": "PUT",
                "url": loggable_url(url),
                "timeout": timeout,
                "error_type": type(exc).__name__,
            },
            exc_info=_redacted_exc_info(exc),
        )
        raise
