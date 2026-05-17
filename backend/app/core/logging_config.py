"""
SAR Irrigation Scheduling System — Logging Configuration.

Sets up structured logging with:
- Console output (colored, human-readable)
- File output (JSON-structured, rotated)
- Module-level logger factory
"""

import logging
import logging.handlers
import sys
from pathlib import Path

from app.core.config import settings


# ---------------------------------------------------------------------------
# Log format strings
# ---------------------------------------------------------------------------
CONSOLE_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
)
FILE_FORMAT = (
    '{"timestamp":"%(asctime)s","level":"%(levelname)s",'
    '"logger":"%(name)s","message":"%(message)s"}'
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> None:
    """
    Configure the root logger with console and file handlers.

    Called once at application startup from main.py.
    Creates the logs directory if it does not exist.
    """
    # Ensure logs directory exists
    logs_dir = Path(settings.logs_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Determine log level from settings
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # ── Root logger ──────────────────────────────────────────────────
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove any existing handlers to avoid duplicate output on reload
    root_logger.handlers.clear()

    # ── Console handler ──────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(
        logging.Formatter(CONSOLE_FORMAT, datefmt=DATE_FORMAT)
    )
    root_logger.addHandler(console_handler)

    # ── File handler (rotating) ──────────────────────────────────────
    log_file = logs_dir / "app.log"
    file_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_file),
        maxBytes=10 * 1024 * 1024,  # 10 MB per file
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(
        logging.Formatter(FILE_FORMAT, datefmt=DATE_FORMAT)
    )
    root_logger.addHandler(file_handler)

    # ── Suppress noisy third-party loggers ───────────────────────────
    for noisy_logger in ("uvicorn.access", "asyncio", "sqlalchemy.engine"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    root_logger.info(
        "Logging initialized — level=%s, file=%s",
        settings.log_level,
        log_file,
    )


def get_logger(name: str) -> logging.Logger:
    """
    Create a named logger for a module.

    Usage:
        from app.core.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("Processing started")

    Args:
        name: Usually ``__name__`` of the calling module.

    Returns:
        A configured ``logging.Logger`` instance.
    """
    return logging.getLogger(name)
