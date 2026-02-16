from __future__ import annotations

import io
import logging
from typing import Tuple

import httpx
from PIL import Image

from core.utils.http import loggable_url

logger = logging.getLogger(__name__)


def fetch_and_standardize_image(
    image_url: str,
    target_size: Tuple[int, int] = (1024, 1024),
    timeout_s: float = 20.0,
) -> tuple[bytes, str, tuple[int, int]]:
    """
    Fetch image from URL, convert to RGB, resize to target_size (square), return PNG bytes.
    """
    try:
        with httpx.Client(timeout=timeout_s, follow_redirects=True) as client:
            response = client.get(image_url)
            response.raise_for_status()
            raw = response.content
    except httpx.HTTPError as exc:
        logger.error(
            "image fetch failed",
            extra={
                "url": loggable_url(image_url),
                "timeout": timeout_s,
                "error_type": type(exc).__name__,
            },
        )
        raise

    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img = img.resize(target_size, Image.Resampling.LANCZOS)

    out = io.BytesIO()
    img.save(out, format="PNG", optimize=True)
    png_bytes = out.getvalue()

    logger.info(
        "Fetched image %s -> standardized to %s",
        loggable_url(image_url),
        target_size,
    )
    return png_bytes, img.mode, img.size
