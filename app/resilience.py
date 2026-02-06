"""
Resilience utilities for Hammy the Hire Tracker.

Provides retry logic with exponential backoff, rate limiting,
and circuit breaker patterns for production reliability.
"""

import time
import random
import functools
import threading
from typing import Callable, Optional, Type, Tuple, Any
from datetime import datetime, timedelta
from collections import deque

from app.logging_config import get_logger

logger = get_logger(__name__)


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, message: str, last_exception: Optional[Exception] = None):
        super().__init__(message)
        self.last_exception = last_exception


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """
    Decorator for retry with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap in seconds
        exponential_base: Base for exponential calculation
        jitter: Add random jitter to prevent thundering herd
        retryable_exceptions: Tuple of exceptions to retry on
        on_retry: Optional callback called on each retry (exception, attempt)

    Usage:
        @retry_with_backoff(max_retries=3, base_delay=1.0)
        def flaky_api_call():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"All {max_retries} retries exhausted for {func.__name__}: {e}"
                        )
                        raise RetryError(
                            f"Failed after {max_retries} retries: {e}", last_exception=e
                        )

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base**attempt), max_delay)

                    # Add jitter (±25% of delay)
                    if jitter:
                        delay = delay * (0.75 + random.random() * 0.5)

                    logger.warning(
                        f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                        f"after {delay:.2f}s delay. Error: {e}"
                    )

                    if on_retry:
                        on_retry(e, attempt + 1)

                    time.sleep(delay)

            raise RetryError(f"Failed after {max_retries} retries", last_exception=last_exception)

        return wrapper

    return decorator


class RateLimiter:
    """
    Token bucket rate limiter for API calls.

    Implements a sliding window rate limiter that allows bursting
    while maintaining an average rate limit.
    """

    def __init__(
        self,
        calls_per_minute: int = 60,
        burst_size: Optional[int] = None,
    ):
        """
        Initialize rate limiter.

        Args:
            calls_per_minute: Maximum calls allowed per minute
            burst_size: Maximum burst size (defaults to calls_per_minute / 4)
        """
        self.calls_per_minute = calls_per_minute
        self.burst_size = burst_size or max(1, calls_per_minute // 4)
        self.min_interval = 60.0 / calls_per_minute  # seconds between calls

        self._lock = threading.Lock()
        self._call_times: deque = deque(maxlen=calls_per_minute)
        self._last_call: Optional[float] = None

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire permission to make a call, blocking if necessary.

        Args:
            timeout: Maximum time to wait in seconds (None for infinite)

        Returns:
            True if acquired, False if timeout exceeded
        """
        start_time = time.time()

        while True:
            with self._lock:
                now = time.time()

                # Remove old calls outside the window
                while self._call_times and self._call_times[0] < now - 60:
                    self._call_times.popleft()

                # Check if we can proceed
                if len(self._call_times) < self.calls_per_minute:
                    # Also respect minimum interval for burst control
                    if self._last_call is None or (now - self._last_call) >= self.min_interval:
                        self._call_times.append(now)
                        self._last_call = now
                        return True

                # Calculate wait time
                if self._call_times:
                    oldest_call = self._call_times[0]
                    wait_for_window = max(0, oldest_call + 60 - now)
                else:
                    wait_for_window = 0

                if self._last_call:
                    wait_for_interval = max(0, self._last_call + self.min_interval - now)
                else:
                    wait_for_interval = 0

                wait_time = max(wait_for_window, wait_for_interval)

            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed + wait_time > timeout:
                    return False

            # Sleep and retry
            if wait_time > 0:
                time.sleep(min(wait_time, 0.1))  # Check frequently
            else:
                time.sleep(0.01)  # Brief yield

    def __call__(self, func: Callable) -> Callable:
        """Use as decorator."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.acquire()
            return func(*args, **kwargs)

        return wrapper


class CircuitBreaker:
    """
    Circuit breaker pattern for failing fast on repeated errors.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Circuit is broken, requests fail immediately
    - HALF_OPEN: Testing if service recovered
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        success_threshold: int = 2,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
            success_threshold: Successes needed to close circuit
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self._state = self.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        """Get current circuit state."""
        with self._lock:
            if self._state == self.OPEN:
                # Check if recovery timeout has passed
                if (
                    self._last_failure_time
                    and time.time() - self._last_failure_time >= self.recovery_timeout
                ):
                    self._state = self.HALF_OPEN
                    self._success_count = 0
            return self._state

    def record_success(self):
        """Record a successful call."""
        with self._lock:
            if self._state == self.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = self.CLOSED
                    self._failure_count = 0
                    logger.info("Circuit breaker closed after successful recovery")
            elif self._state == self.CLOSED:
                self._failure_count = 0

    def record_failure(self):
        """Record a failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == self.HALF_OPEN:
                self._state = self.OPEN
                logger.warning("Circuit breaker re-opened after failure in half-open state")
            elif self._state == self.CLOSED and self._failure_count >= self.failure_threshold:
                self._state = self.OPEN
                logger.warning(f"Circuit breaker opened after {self._failure_count} failures")

    def __call__(self, func: Callable) -> Callable:
        """Use as decorator."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == self.OPEN:
                raise RetryError("Circuit breaker is open - service temporarily unavailable")

            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except Exception as e:
                self.record_failure()
                raise

        return wrapper


# Pre-configured rate limiters for common use cases
class APIRateLimiters:
    """Pre-configured rate limiters for different APIs."""

    # Claude API: Be conservative (60 calls/minute)
    claude = RateLimiter(calls_per_minute=60, burst_size=10)

    # OpenAI API: Similar limits
    openai = RateLimiter(calls_per_minute=60, burst_size=10)

    # Google/Gemini API: More generous limits
    gemini = RateLimiter(calls_per_minute=90, burst_size=15)

    # Gmail API: Very conservative (10 calls/minute to be safe)
    gmail = RateLimiter(calls_per_minute=10, burst_size=3)

    # Web scraping: Very conservative
    web_scrape = RateLimiter(calls_per_minute=20, burst_size=5)


# Convenience function for making resilient API calls
def resilient_call(
    func: Callable,
    *args,
    max_retries: int = 3,
    rate_limiter: Optional[RateLimiter] = None,
    **kwargs,
) -> Any:
    """
    Make a resilient API call with retry and rate limiting.

    Args:
        func: Function to call
        *args: Positional arguments for func
        max_retries: Number of retries
        rate_limiter: Optional rate limiter to use
        **kwargs: Keyword arguments for func

    Returns:
        Result of func call
    """
    if rate_limiter:
        rate_limiter.acquire()

    @retry_with_backoff(max_retries=max_retries)
    def _call():
        return func(*args, **kwargs)

    return _call()
