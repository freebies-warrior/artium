from __future__ import annotations

from types import TracebackType


def redacted_exc_info(
    exc: BaseException,
    *,
    include_traceback: bool = True,
) -> tuple[type[BaseException], BaseException, TracebackType | None]:
    """Build exc_info tuple while redacting exception message text."""
    try:
        redacted: BaseException = type(exc)()
    except Exception:
        redacted = Exception(type(exc).__name__)
    traceback = exc.__traceback__ if include_traceback else None
    return type(exc), redacted, traceback
