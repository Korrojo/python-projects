from __future__ import annotations

import logging
import logging.config
from datetime import datetime
from pathlib import Path

_RUN_TS: str | None = None


def get_run_timestamp() -> str:
    """Return a stable timestamp string for the current process run.

    The first call fixes the timestamp and subsequent calls return the same value.
    """
    global _RUN_TS
    if _RUN_TS is None:
        _RUN_TS = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _RUN_TS


def _default_log_dir() -> Path:
    # Default to ./logs in the current working directory
    return Path.cwd() / "logs"


def setup_logging(
    log_dir: Path | None = None,
    level: str = "INFO",
    json_logs: bool = False,
    file_name: str | None = None,
) -> None:
    """Configure logging with console + rotating file handlers.

    Args:
        log_dir: Directory for log files (default: ./logs)
        level: Root logging level (e.g., "INFO", "DEBUG")
        json_logs: If True, use a simple JSON-like format for structured logs
    """
    log_dir = log_dir or _default_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)

    run_ts = get_run_timestamp()
    effective_file_name = file_name or f"{run_ts}_app.log"
    file_path = log_dir / effective_file_name

    if json_logs:
        formatter = {
            "()": "logging.Formatter",
            "fmt": (
                "{"  # compact JSON-like
                '"ts": "%(asctime)s", '
                '"lvl": "%(levelname)s", '
                '"name": "%(name)s", '
                '"msg": "%(message)s"'
                "}"
            ),
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        }
    else:
        formatter = {
            "()": "logging.Formatter",
            "fmt": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"standard": formatter},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "standard",
                "filename": str(file_path),
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "root": {
            "level": level,
            "handlers": ["console", "file"],
        },
    }

    logging.config.dictConfig(config)


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name)
