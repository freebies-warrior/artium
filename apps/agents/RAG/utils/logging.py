from __future__ import annotations

import logging

from core.settings import get_settings


def setup_logging(level: str = None) -> None:
    if level is None:
        level = get_settings().LOG_LEVEL
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
