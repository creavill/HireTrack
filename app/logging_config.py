"""
Centralized logging configuration for Hammy the Hire Tracker.

Provides structured logging with proper levels, file rotation,
and JSON formatting for production use.
"""

import logging
import logging.handlers
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

# Log directory
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Log levels by environment
LOG_LEVELS = {
    "development": logging.DEBUG,
    "production": logging.INFO,
    "testing": logging.WARNING,
}


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_data"):
            log_obj["data"] = record.extra_data

        return json.dumps(log_obj)


class ConsoleFormatter(logging.Formatter):
    """Colored console formatter for development."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Truncate long messages for console
        message = record.getMessage()
        if len(message) > 500:
            message = message[:500] + "..."

        return f"{color}[{timestamp}] {record.levelname:8}{self.RESET} {record.name}: {message}"


def setup_logging(
    level: Optional[str] = None,
    json_logs: bool = False,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Configure application-wide logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Use JSON formatting (for production)
        log_file: Optional log file path (enables file logging)

    Returns:
        Root logger configured for the application
    """
    # Determine environment and log level
    env = os.environ.get("FLASK_ENV", "development")
    if level:
        log_level = getattr(logging, level.upper(), logging.INFO)
    else:
        log_level = LOG_LEVELS.get(env, logging.INFO)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    if json_logs:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(ConsoleFormatter())

    root_logger.addHandler(console_handler)

    # File handler with rotation
    if log_file or env == "production":
        file_path = log_file or str(LOGS_DIR / "app.log")
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding extra data to log messages."""

    def __init__(self, logger: logging.Logger, **kwargs):
        self.logger = logger
        self.extra_data = kwargs
        self.old_factory = None

    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()
        extra = self.extra_data

        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            record.extra_data = extra
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)


# Operation logger for tracking scan operations
class OperationLogger:
    """Logger for tracking long-running operations like email scans."""

    def __init__(self, operation_type: str):
        self.operation_type = operation_type
        self.start_time = datetime.now()
        self.log_file = (
            LOGS_DIR / f"{operation_type}_{self.start_time.strftime('%Y%m%d_%H%M%S')}.log"
        )
        self.logger = get_logger(f"operation.{operation_type}")
        self.entries = []

    def log(self, message: str, level: str = "INFO", **data):
        """Log an operation message."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            **data,
        }
        self.entries.append(entry)

        # Also log to standard logger
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(f"[{self.operation_type}] {message}", extra={"data": data} if data else {})

        # Write to operation log file
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def info(self, message: str, **data):
        self.log(message, "INFO", **data)

    def warning(self, message: str, **data):
        self.log(message, "WARNING", **data)

    def error(self, message: str, **data):
        self.log(message, "ERROR", **data)

    def success(self, message: str, **data):
        self.log(message, "INFO", status="success", **data)

    def get_summary(self) -> dict:
        """Get operation summary."""
        duration = (datetime.now() - self.start_time).total_seconds()
        errors = [e for e in self.entries if e.get("level") == "ERROR"]
        warnings = [e for e in self.entries if e.get("level") == "WARNING"]

        return {
            "operation": self.operation_type,
            "started_at": self.start_time.isoformat(),
            "duration_seconds": round(duration, 2),
            "total_entries": len(self.entries),
            "errors": len(errors),
            "warnings": len(warnings),
            "log_file": str(self.log_file),
        }
