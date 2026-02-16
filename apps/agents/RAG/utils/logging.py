from __future__ import annotations

from core.logging import configure_logging
from core.settings import get_settings


def setup_logging(level: str | None = None) -> None:
    configure_logging(level or get_settings().LOG_LEVEL)
