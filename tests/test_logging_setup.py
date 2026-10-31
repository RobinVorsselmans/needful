import logging

from needful.logging_setup import setup_logging


def test_level_comes_from_env(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "debug")
    setup_logging()
    logger = logging.getLogger("needful")
    assert logger.level == logging.DEBUG


def test_default_level_is_info(monkeypatch):
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    setup_logging()
    logger = logging.getLogger("needful")
    assert logger.level == logging.INFO
