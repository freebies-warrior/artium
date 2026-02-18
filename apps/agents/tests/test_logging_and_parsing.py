import logging

import pytest

import agents.core.logging as core_logging


def test_configure_logging_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(core_logging, "_configured_level", None)

    core_logging.configure_logging("INFO")
    first_handlers = tuple(id(handler) for handler in logging.getLogger().handlers)
    core_logging.configure_logging("INFO")
    second_handlers = tuple(id(handler) for handler in logging.getLogger().handlers)

    assert first_handlers == second_handlers
