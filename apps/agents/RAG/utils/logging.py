from __future__ import annotations

from agents.core.logging import configure_logging
from agents.core.settings import get_settings


def setup_logging(level: str | None = None) -> None:
    configure_logging(level or get_settings().LOG_LEVEL)
