from __future__ import annotations

import logging
from logging.config import dictConfig
from threading import Lock

_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_config_lock = Lock()
_configured_level: str | None = None


def _normalize_level(level: str | None) -> str:
    if not level:
        return "INFO"
    normalized = level.upper()
    if normalized in logging._nameToLevel:
        return normalized
    return "INFO"


def configure_logging(level: str) -> None:
    """Configure application logging in a consistent, idempotent way."""
    normalized_level = _normalize_level(level)

    global _configured_level
    with _config_lock:
        if _configured_level == normalized_level:
            return

        dictConfig(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "standard": {
                        "format": _LOG_FORMAT,
                        "datefmt": _DATE_FORMAT,
                    }
                },
                "handlers": {
                    "default": {
                        "class": "logging.StreamHandler",
                        "formatter": "standard",
                        "stream": "ext://sys.stderr",
                    }
                },
                "root": {
                    "level": normalized_level,
                    "handlers": ["default"],
                },
                "loggers": {
                    "uvicorn": {
                        "handlers": ["default"],
                        "level": normalized_level,
                        "propagate": False,
                    },
                    "uvicorn.error": {
                        "handlers": ["default"],
                        "level": normalized_level,
                        "propagate": False,
                    },
                    "uvicorn.access": {
                        "handlers": ["default"],
                        "level": normalized_level,
                        "propagate": False,
                    },
                },
            }
        )

        _configured_level = normalized_level
