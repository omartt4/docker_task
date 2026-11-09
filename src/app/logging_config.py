"""Application logging configuration."""

from __future__ import annotations

import logging
import os


DEFAULT_LOG_LEVEL = "INFO"


def configure_logging(level: str | None = None) -> None:
    """Configure level-aware, consistently formatted application logging."""
    selected_level = (level or os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL)).upper()
    if selected_level not in logging.getLevelNamesMapping():
        raise ValueError(f"Unsupported log level: {selected_level}")
    logging.basicConfig(
        level=selected_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        force=True,
    )
