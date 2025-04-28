"""
Rate limiter for API calls to respect service limits.
"""

import time
from threading import Lock
from statistics import mean
from typing import Optional

from repo_organizer.utils.exceptions import RateLimitExceededError


class RateLimiter:
    """Rate limiter for API calls to respect service limits."""

    def __init__(
        self,
        calls_per_minute: int = 60,
        name: str = "API",
        max_wait_time: Optional[float] = None,
        fail_on_limit: bool = False,
    ):
        """Initialize rate limiter.

        Args:
            calls_per_minute: Maximum number of calls allowed per minute
            name: Name of the API being rate limited (for logging)
            max_wait_time: Maximum time to wait in seconds (None for unlimited)
            fail_on_limit: If True, raise an exception instead of waiting when limit exceeded
        """
        self.calls_per_minute = calls_per_minute
        self.interval = 60.0 / calls_per_minute  # Time between calls in seconds
        self.last_call_time = 0.0
        self.lock = Lock()
        self.name = name
        self.wait_times = []
        self.total_waits = 0
        self.total_calls = 0
        self.max_wait_time = max_wait_time
        self.fail_on_limit = fail_on_limit
        self.rate_limit_exceptions = 0

    def wait(self, logger=None, debug=False):
        """Wait until next call is allowed according to rate limits.

        Args:
            logger: Optional logger to log rate limiting events
            debug: Whether to enable debug logging for waits

        Returns:
            Time waited in seconds

        Raises:
            RateLimitExceededError: If fail_on_limit is True and wait time exceeds max_wait_time
        """
        with self.lock:
            current_time = time.time()
            elapsed = current_time - self.last_call_time
            wait_time = 0

            if elapsed < self.interval:
                wait_time = self.interval - elapsed

                # Check if wait time exceeds max_wait_time
                if self.max_wait_time is not None and wait_time > self.max_wait_time:
                    if self.fail_on_limit:
                        self.rate_limit_exceptions += 1
                        error_msg = (
                            f"Rate limit exceeded for {self.name} API: would need to wait {wait_time:.2f}s, "
                            f"max allowed is {self.max_wait_time:.2f}s"
                        )
                        if logger:
                            logger.log(error_msg, level="error")
                        raise RateLimitExceededError(error_msg)
                    else:
                        # Cap wait time at max_wait_time
                        wait_time = self.max_wait_time
                        if logger:
                            logger.log(
                                f"Rate limit: Capping wait time to {wait_time:.2f}s for {self.name} API",
                                level="warning" if debug else "info",
                            )

                if logger and debug:
                    logger.log(
                        f"Rate limit: Waiting {wait_time:.2f}s for {self.name} API",
                        level="debug",
                    )
                time.sleep(wait_time)
                self.wait_times.append(wait_time)
                self.total_waits += 1

            self.last_call_time = time.time()
            self.total_calls += 1
            return wait_time

    def get_stats(self) -> dict:
        """Get statistics about rate limiting.

        Returns:
            Dictionary of rate limiting statistics
        """
        avg_wait = mean(self.wait_times) if self.wait_times else 0
        return {
            "name": self.name,
            "calls_per_minute": self.calls_per_minute,
            "total_calls": self.total_calls,
            "total_waits": self.total_waits,
            "total_wait_time": sum(self.wait_times),
            "avg_wait_time": avg_wait,
            "pct_rate_limited": (self.total_waits / self.total_calls * 100)
            if self.total_calls
            else 0,
            "rate_limit_exceptions": self.rate_limit_exceptions,
            "max_wait_time": self.max_wait_time,
            "fail_on_limit": self.fail_on_limit,
        }
