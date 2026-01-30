from __future__ import annotations

import io
import logging
from typing import Tuple

import httpx
from PIL import Image

logger = logging.getLogger(__name__)


def fetch_and_standardize_image(
    image_url: str,
    target_size: Tuple[int, int] = (1024, 1024),
    timeout_s: float = 20.0,
) -> tuple[bytes, str, tuple[int, int]]:
    """
    Fetch image from URL, convert to RGB, resize to target_size (square), return PNG bytes.
    """
    with httpx.Client(timeout=timeout_s, follow_redirects=True) as client:
        r = client.get(image_url)
        r.raise_for_status()
        raw = r.content

    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img = img.resize(target_size, Image.Resampling.LANCZOS)

    out = io.BytesIO()
    img.save(out, format="PNG", optimize=True)
    png_bytes = out.getvalue()

    logger.info("Fetched image %s -> standardized to %s", image_url, target_size)
    return png_bytes, img.mode, img.size
