"""Application logging configuration."""

from __future__ import annotations

import logging


def configure_logging() -> None:
    """Configure basic application logging."""
    logging.basicConfig(level=logging.INFO)
