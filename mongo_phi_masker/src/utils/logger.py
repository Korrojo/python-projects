"""
Logger utility for MongoDB PHI masking pipeline.

This module configures logging for the application with support for:
- Console and file outputs
- Log rotation
- Different log levels by component
- Colored console output
"""

import datetime
import logging
import logging.handlers
import os
import sys
from typing import Any, cast

import multiprocessing_logging


class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to console log messages."""

    # ANSI color codes
    COLORS = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "bold": "\033[1m",
        "reset": "\033[0m",
    }

    def __init__(
        self,
        fmt: str,
        datefmt: str | None = None,
        style: str = "%",
        color_config: dict[str, str] | None = None,
        style_config: dict[str, str] | None = None,
        separator: str = " | ",
    ):
        """Initialize the formatter with format and color configuration.

        Args:
            fmt: The log message format string
            datefmt: The date format string
            style: The style of the format string
            color_config: Mapping of log levels to colors
            style_config: Mapping of log components to style
            separator: Separator for styled components
        """
        # Cast style to the expected literal type for logging.Formatter
        super().__init__(fmt, datefmt, cast(Any, style))
        self.color_config = color_config or {
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red bold",
        }
        self.style_config = style_config or {
            "timestamp": "blue",
            "level": "yellow bold",
            "name": "cyan",
        }
        self.separator = separator

    def _colorize(self, text: str, color_spec: str) -> str:
        """Apply ANSI color codes to text based on color specification.

        Args:
            text: The text to colorize
            color_spec: Color specification (e.g., "red bold")

        Returns:
            The colorized text
        """
        if not color_spec:
            return text

        color_codes = []
        for spec in color_spec.split():
            if spec in self.COLORS:
                color_codes.append(self.COLORS[spec])

        if not color_codes:
            return text

        return f"{''.join(color_codes)}{text}{self.COLORS['reset']}"

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors.

        Args:
            record: The log record to format

        Returns:
            The formatted log message
        """
        # Save the original
        orig_msg = record.msg
        orig_levelname = record.levelname

        # Apply colors to level name
        if record.levelname in self.color_config:
            record.levelname = self._colorize(record.levelname, self.color_config[record.levelname])

        # Format record
        result = super().format(record)

        # Restore originals
        record.msg = orig_msg
        record.levelname = orig_levelname

        return result


class LoggerFactory:
    """Factory class for creating and configuring loggers."""

    _configured_loggers: dict[str, logging.Logger] = {}
    _config: dict[str, Any] = {}

    @classmethod
    def configure(cls, config: dict[str, Any]) -> None:
        """Configure the logger factory with settings.

        Args:
            config: The logging configuration dictionary
        """
        cls._config = config
        # Initialize multiprocessing logging support
        multiprocessing_logging.install_mp_handler()

    @classmethod
    def get_logger(cls, name: str, component: str | None = None) -> logging.Logger:
        """Get a logger configured according to settings.

        Args:
            name: The logger name
            component: Optional component (masking, indexing, etc.)

        Returns:
            A configured logger instance
        """
        if not cls._config:
            raise ValueError("Logger not configured. Call configure() first.")

        logger_key = f"{name}:{component}" if component else name

        if logger_key in cls._configured_loggers:
            return cls._configured_loggers[logger_key]

        logger = logging.getLogger(name)

        # Clear existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Set level
        logger.setLevel(logging.DEBUG)  # Let handlers control level

        # Configure console handler
        cls._add_console_handler(logger)

        # Add component-specific file handler if applicable
        if component and component in cls._config:
            cls._add_file_handler(logger, component)
        else:
            # Use base file handler
            cls._add_file_handler(logger, "base")

        cls._configured_loggers[logger_key] = logger
        return logger

    @classmethod
    def _add_console_handler(cls, logger: logging.Logger) -> None:
        """Add a console handler to the logger.

        Args:
            logger: The logger to add the handler to
        """
        console_config = cls._config.get("base", {}).get("console", {})
        level = getattr(logging, console_config.get("level", "INFO"))

        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        formatter = ColoredFormatter(
            fmt=console_config.get("format", "%(asctime)s | %(levelname)s | %(message)s"),
            datefmt=console_config.get("date_format", "%Y-%m-%d %H:%M:%S"),
            color_config=console_config.get("colors"),
            style_config=console_config.get("styles"),
            separator=console_config.get("separator", " | "),
        )

        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    @classmethod
    def _add_file_handler(cls, logger: logging.Logger, component: str) -> None:
        """Add a file handler to the logger.

        Args:
            logger: The logger to add the handler to
            component: The component config to use
        """
        component_config = cls._config.get(component, {})
        base_config = cls._config.get("base", {})

        # Get component-specific settings or fall back to base settings
        level = getattr(logging, component_config.get("level", base_config.get("level", "INFO")))

        # Create log directory if it doesn't exist
        log_dir = component_config.get("directory", "logs")
        os.makedirs(log_dir, exist_ok=True)

        # Generate filename with timestamp
        filename = component_config.get("filename", f"{component}_%Y%m%d_%H%M%S.log")
        datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = datetime.datetime.now().strftime(filename)
        log_path = os.path.join(log_dir, filename)

        # Create a rotating file handler
        max_bytes = component_config.get("max_bytes", base_config.get("max_bytes", 10485760))
        backup_count = component_config.get("backup_count", base_config.get("backup_count", 3))

        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=base_config.get("encoding", "utf-8"),
        )

        file_handler.setLevel(level)

        formatter = logging.Formatter(
            fmt=component_config.get("format", "%(asctime)s | %(levelname)s | %(message)s"),
            datefmt=base_config.get("date_format", "%Y-%m-%d %H:%M:%S"),
        )

        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def setup_logging(
    log_level: int | str = "INFO",
    environment: str | None = None,
    log_file: str | None = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB by default
    backup_count: int = 5,  # Keep 5 backup files by default
    use_timed_rotating: bool = False,
) -> str:
    """Set up logging configuration with enhanced rotation capabilities.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) or integer
        environment: Environment name (e.g., DEV, TEST, PROD)
        log_file: Optional custom log file path, overrides default naming
        max_bytes: Maximum size in bytes before rotating the log file
        backup_count: Number of backup files to keep
        use_timed_rotating: Use time-based rotation instead of size-based

    Returns:
        Path to log file
    """
    # Override settings from environment variables if available
    max_bytes = int(os.environ.get("MONGO_PHI_LOG_MAX_BYTES", max_bytes))
    backup_count = int(os.environ.get("MONGO_PHI_LOG_BACKUP_COUNT", backup_count))
    use_timed_rotating = os.environ.get("MONGO_PHI_LOG_TIMED_ROTATION", str(use_timed_rotating)).lower() in (
        "true",
        "1",
        "yes",
    )

    # Get numeric log level (handle both int and str)
    if isinstance(log_level, int):
        numeric_level = log_level
    else:
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            print(f"Invalid log level: {log_level}")
            numeric_level = logging.INFO

    # Get environment name
    env_name = environment.lower() if environment else "default"

    # Create log directory
    log_dir = f"logs/{env_name}"
    os.makedirs(log_dir, exist_ok=True)

    # If log_file is not specified, create a date-based log filename
    if not log_file:
        today = datetime.datetime.now().strftime("%Y%m%d")
        log_file = f"{log_dir}/masking_{today}.log"
    elif not os.path.isabs(log_file):
        # If a relative path is provided, make it relative to the environment log directory
        log_file = os.path.join(log_dir, log_file)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatter matching LOGGING_STANDARD.md
    formatter = logging.Formatter(fmt="%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_level)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    if use_timed_rotating:
        # Time-based rotation (midnight)
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_file, when="midnight", interval=1, backupCount=backup_count  # Rotate daily
        )
        rotation_type = "time-based (daily)"
    else:
        # Size-based rotation
        file_handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
        rotation_type = f"size-based ({max_bytes/1024/1024:.1f}MB)"

    file_handler.setFormatter(formatter)
    file_handler.setLevel(numeric_level)
    root_logger.addHandler(file_handler)

    # Support logging in multi-process environments
    try:
        import multiprocessing_logging

        multiprocessing_logging.install_mp_handler()
    except (ImportError, Exception) as e:
        logging.warning(f"Multiprocessing logging support not available: {str(e)}")

    # Create symlink to latest log file for convenience
    if sys.platform != "win32":
        latest_link = f"{log_dir}/masking_latest.log"
        if os.path.exists(latest_link):
            try:
                os.remove(latest_link)
            except Exception as e:
                logging.warning(f"Could not remove old symlink: {str(e)}")

        try:
            # Create relative symlink (relative to the log directory)
            log_file_name = os.path.basename(log_file)
            os.symlink(log_file_name, latest_link)
        except Exception as e:
            logging.warning(f"Could not create symlink to latest log: {str(e)}")

    # Cleanup old log files (keep last 30 days)
    try:
        log_files = [
            f
            for f in os.listdir(log_dir)
            if f.startswith("masking_") and f.endswith(".log") and f != "masking_latest.log"
        ]
        if len(log_files) > 30:
            log_files.sort()
            for old_file in log_files[:-30]:
                file_path = os.path.join(log_dir, old_file)
                os.remove(file_path)
                logging.debug(f"Removed old log file: {file_path}")
    except Exception as e:
        logging.warning(f"Error during log cleanup: {str(e)}")

    logging.info(f"Logging initialized at level {log_level}")
    logging.info(f"Log file: {log_file} with {rotation_type} rotation (keeping {backup_count} backups)")

    return log_file
