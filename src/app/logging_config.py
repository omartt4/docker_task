"""Application logging configuration."""

from __future__ import annotations

import logging
import logging.config
import os
from pathlib import Path


DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FILE = "logs/app.log"


def configure_logging(
    level: str | None = None,
    log_file: str | Path | None = None,
) -> None:
    """Configure console and rotating-file handlers for the application."""
    selected_level = (level or os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL)).upper()
    if selected_level not in logging.getLevelNamesMapping():
        raise ValueError(f"Unsupported log level: {selected_level}")

    selected_file = Path(log_file or os.getenv("LOG_FILE", DEFAULT_LOG_FILE))
    selected_file.parent.mkdir(parents=True, exist_ok=True)

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                    "datefmt": "%Y-%m-%dT%H:%M:%S%z",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": selected_level,
                    "formatter": "standard",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": selected_level,
                    "formatter": "standard",
                    "filename": str(selected_file),
                    "maxBytes": 1_048_576,
                    "backupCount": 3,
                    "encoding": "utf-8",
                },
            },
            "root": {
                "level": selected_level,
                "handlers": ["console", "file"],
            },
        }
    )
