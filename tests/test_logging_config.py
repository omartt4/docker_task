import logging

import pytest

from app.logging_config import configure_logging


def test_logging_writes_formatted_messages_to_file(tmp_path, caplog) -> None:
    log_file = tmp_path / "application.log"
    configure_logging(level="INFO", log_file=log_file)
    logger = logging.getLogger("test.logging")

    logger.info("logging validation passed")

    assert "logging validation passed" in log_file.read_text(encoding="utf-8")
    assert "INFO" in log_file.read_text(encoding="utf-8")


def test_logging_rejects_unknown_level(tmp_path) -> None:
    with pytest.raises(ValueError, match="Unsupported log level"):
        configure_logging(level="NOT_A_LEVEL", log_file=tmp_path / "application.log")
