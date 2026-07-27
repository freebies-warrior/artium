from __future__ import annotations

import base64
from typing import Tuple


def data_url_to_bytes(data_url: str) -> Tuple[bytes, str]:
    # supports data:<mime>;base64,<...>
    header, b64 = data_url.split(",", 1)
    mime = header.split(";")[0].split(":", 1)[1]
    return base64.b64decode(b64), mime
