from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import Tuple

from PIL import Image
import io


def load_image_bytes(path: str | Path) -> Tuple[bytes, str]:
    p = Path(path)
    b = p.read_bytes()
    mime, _ = mimetypes.guess_type(str(p))
    return b, (mime or "application/octet-stream")


def pil_from_bytes(image_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


def bytes_to_data_url(image_bytes: bytes, mime_type: str = "image/png") -> str:
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"


def data_url_to_bytes(data_url: str) -> Tuple[bytes, str]:
    # supports data:<mime>;base64,<...>
    header, b64 = data_url.split(",", 1)
    mime = header.split(";")[0].split(":", 1)[1]
    return base64.b64decode(b64), mime
