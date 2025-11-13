"""Logging utilities for centralized log management."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from utils.paths import get_logs_dir


def setup_logging(
    operation: str,
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    verbose: bool = False,
) -> logging.Logger:
    """Set up logging to centralized logs directory.

    Args:
        operation: Operation name (dump, restore, export, import)
        log_file: Optional custom log file path (defaults to centralized logs)
        level: Logging level
        verbose: Enable verbose console output

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(f"mongo_backup_tools.{operation}")
    logger.setLevel(logging.DEBUG if verbose else level)

    # Clear existing handlers
    logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if verbose else logging.WARNING)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (centralized logs)
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = get_logs_dir() / f"{timestamp}_{operation}.log"

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    logger.info(f"Logging initialized for operation: {operation}")
    logger.info(f"Log file: {log_file}")

    return logger


def get_logger(operation: str) -> logging.Logger:
    """Get existing logger for operation.

    Args:
        operation: Operation name (dump, restore, export, import)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"mongo_backup_tools.{operation}")
