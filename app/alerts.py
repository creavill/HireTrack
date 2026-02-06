"""
Error Alerting System for Hammy the Hire Tracker.

Provides centralized error tracking, alerting, and notification
capabilities for production monitoring.

Current implementation logs to file and console.
Can be extended with email, Slack, or webhook notifications.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from collections import deque
import threading

from app.logging_config import get_logger, LOGS_DIR

logger = get_logger(__name__)


class ErrorTracker:
    """
    Tracks errors and provides alerting capabilities.

    Features:
    - Maintains recent error history in memory
    - Persists errors to log file
    - Detects error patterns and spikes
    - Can trigger alerts (extensible)
    """

    def __init__(
        self,
        max_history: int = 100,
        alert_threshold: int = 5,
        alert_window_seconds: int = 60,
    ):
        """
        Initialize error tracker.

        Args:
            max_history: Maximum errors to keep in memory
            alert_threshold: Number of errors in window to trigger alert
            alert_window_seconds: Time window for counting errors
        """
        self.max_history = max_history
        self.alert_threshold = alert_threshold
        self.alert_window_seconds = alert_window_seconds

        self._errors: deque = deque(maxlen=max_history)
        self._lock = threading.Lock()
        self._alert_handlers: List[callable] = []
        self._error_log_file = LOGS_DIR / "errors.jsonl"

        # Ensure log directory exists
        LOGS_DIR.mkdir(exist_ok=True)

    def record_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: str = "error",
        operation: Optional[str] = None,
    ) -> Dict:
        """
        Record an error occurrence.

        Args:
            error: The exception that occurred
            context: Additional context about the error
            severity: Error severity (error, warning, critical)
            operation: What operation was being performed

        Returns:
            Error record dictionary
        """
        timestamp = datetime.utcnow()

        error_record = {
            "timestamp": timestamp.isoformat() + "Z",
            "severity": severity,
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
        }

        with self._lock:
            self._errors.append(error_record)

        # Persist to log file
        self._persist_error(error_record)

        # Log to standard logger
        log_message = f"[{severity.upper()}] {operation or 'unknown'}: {error}"
        if severity == "critical":
            logger.critical(log_message)
        elif severity == "error":
            logger.error(log_message)
        else:
            logger.warning(log_message)

        # Check if we need to trigger an alert
        self._check_alert_condition()

        return error_record

    def _persist_error(self, error_record: Dict):
        """Persist error to log file."""
        try:
            with open(self._error_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(error_record) + "\n")
        except Exception as e:
            logger.warning(f"Could not persist error to file: {e}")

    def _check_alert_condition(self):
        """Check if error rate exceeds threshold and trigger alert."""
        with self._lock:
            if not self._errors:
                return

            now = datetime.utcnow()
            window_start = now.timestamp() - self.alert_window_seconds

            # Count recent errors
            recent_errors = sum(
                1
                for e in self._errors
                if datetime.fromisoformat(e["timestamp"].replace("Z", "")).timestamp()
                > window_start
            )

            if recent_errors >= self.alert_threshold:
                self._trigger_alert(recent_errors)

    def _trigger_alert(self, error_count: int):
        """Trigger an alert for high error rate."""
        alert_message = (
            f"HIGH ERROR RATE: {error_count} errors in last " f"{self.alert_window_seconds} seconds"
        )
        logger.critical(alert_message)

        # Call registered alert handlers
        for handler in self._alert_handlers:
            try:
                handler(alert_message, self.get_recent_errors(10))
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")

    def register_alert_handler(self, handler: callable):
        """
        Register a callback for alerts.

        Handler signature: handler(message: str, recent_errors: List[Dict])
        """
        self._alert_handlers.append(handler)

    def get_recent_errors(self, limit: int = 20) -> List[Dict]:
        """Get recent errors from memory."""
        with self._lock:
            return list(self._errors)[-limit:]

    def get_error_summary(self) -> Dict:
        """Get a summary of error statistics."""
        with self._lock:
            if not self._errors:
                return {
                    "total": 0,
                    "by_severity": {},
                    "by_type": {},
                    "by_operation": {},
                }

            by_severity = {}
            by_type = {}
            by_operation = {}

            for error in self._errors:
                severity = error.get("severity", "unknown")
                error_type = error.get("error_type", "unknown")
                operation = error.get("operation", "unknown")

                by_severity[severity] = by_severity.get(severity, 0) + 1
                by_type[error_type] = by_type.get(error_type, 0) + 1
                by_operation[operation] = by_operation.get(operation, 0) + 1

            return {
                "total": len(self._errors),
                "by_severity": by_severity,
                "by_type": by_type,
                "by_operation": by_operation,
            }

    def clear_errors(self):
        """Clear error history (for testing)."""
        with self._lock:
            self._errors.clear()


# Global error tracker instance
_error_tracker: Optional[ErrorTracker] = None


def get_error_tracker() -> ErrorTracker:
    """Get the global error tracker instance."""
    global _error_tracker
    if _error_tracker is None:
        _error_tracker = ErrorTracker()
    return _error_tracker


def track_error(
    error: Exception,
    context: Optional[Dict] = None,
    severity: str = "error",
    operation: Optional[str] = None,
) -> Dict:
    """
    Convenience function to track an error.

    Args:
        error: The exception
        context: Additional context
        severity: Error severity
        operation: What operation was being performed

    Returns:
        Error record
    """
    tracker = get_error_tracker()
    return tracker.record_error(error, context, severity, operation)


# Decorator for automatic error tracking
def track_errors(operation: str):
    """
    Decorator to automatically track errors from a function.

    Usage:
        @track_errors("email_scan")
        def scan_emails():
            ...
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                track_error(
                    e,
                    context={"args": str(args)[:200], "kwargs": str(kwargs)[:200]},
                    operation=operation,
                )
                raise

        return wrapper

    return decorator


# Example alert handlers (can be extended)


def console_alert_handler(message: str, recent_errors: List[Dict]):
    """Print alert to console (default handler)."""
    print(f"\n{'='*60}")
    print(f"ALERT: {message}")
    print(f"{'='*60}")
    for error in recent_errors[-5:]:
        print(f"  - {error['timestamp']}: {error['error_type']}: {error['error_message'][:100]}")
    print(f"{'='*60}\n")


def file_alert_handler(message: str, recent_errors: List[Dict]):
    """Write alert to dedicated alert log file."""
    alert_file = LOGS_DIR / "alerts.log"
    timestamp = datetime.utcnow().isoformat() + "Z"

    with open(alert_file, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"[{timestamp}] ALERT: {message}\n")
        f.write(f"{'='*60}\n")
        for error in recent_errors[-5:]:
            f.write(
                f"  - {error['timestamp']}: {error['error_type']}: {error['error_message'][:100]}\n"
            )
        f.write(f"{'='*60}\n")


# Register default alert handlers
def setup_default_alerts():
    """Set up default alert handlers."""
    tracker = get_error_tracker()
    tracker.register_alert_handler(console_alert_handler)
    tracker.register_alert_handler(file_alert_handler)
