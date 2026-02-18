from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import requests
from fastapi import HTTPException

from agents.core.utils.http import _redacted_exc_info, loggable_url

logger = logging.getLogger(__name__)


def download_to_temp_file(url: str, *, suffix: str, timeout: float = 30.0) -> Path:
    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException as exc:
        logger.exception(
            "http request failed",
            extra={
                "method": "GET",
                "url": loggable_url(url),
                "timeout": timeout,
                "error_type": type(exc).__name__,
            },
            exc_info=_redacted_exc_info(exc),
        )
        raise

    if response.status_code != 200:
        logger.warning(
            "download request returned non-200 status",
            extra={"method": "GET", "url": loggable_url(url), "status": response.status_code},
        )
        raise HTTPException(
            status_code=400,
            detail=f"Failed to download {loggable_url(url)}: {response.status_code}",
        )
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(response.content)
    tmp.flush()
    tmp.close()
    return Path(tmp.name)


def sanitize_output_filename(
    raw_name: str | None,
    *,
    default_name: str = "preview.jpeg",
    max_name_length: int = 80,
    max_stem_length: int = 60,
    default_suffix: str = ".jpeg",
) -> str:
    base_name = Path(raw_name or default_name).name
    if len(base_name) > max_name_length:
        stem = Path(base_name).stem[:max_stem_length]
        base_name = stem + Path(base_name).suffix
    if not Path(base_name).suffix:
        base_name = f"{base_name}{default_suffix}"
    return base_name


def cleanup_directory(path: Path) -> None:
    try:
        for child in path.iterdir():
            child.unlink()
        path.rmdir()
    except Exception:
        pass
