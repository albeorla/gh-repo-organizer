"""
Rate limiter for API calls to respect service limits.

This module provides rate limiting functionality for API calls to prevent
exceeding service rate limits, with functionality for tracking and reporting
on rate limiting statistics.
"""

import time
from threading import Lock
from statistics import mean
from typing import Any, Dict, Optional

from repo_organizer.infrastructure.logging.logger import Logger


class RateLimiter:
    """Rate limiter for API calls to respect service limits.

    Implements a simple rate limiting mechanism based on time intervals
    between calls, with support for logging and statistics tracking.
    """

    def __init__(self, calls_per_minute: int = 60, name: str = "API"):
        """Initialize rate limiter.

        Args:
            calls_per_minute: Maximum number of calls allowed per minute
            name: Name of the API being rate limited (for logging)
        """
        self.calls_per_minute = calls_per_minute
        self.interval = 60.0 / calls_per_minute  # Time between calls in seconds
        self.last_call_time = 0.0
        self.lock = Lock()
        self.name = name
        self.wait_times = []
        self.total_waits = 0
        self.total_calls = 0

    def wait(self, logger: Optional[Logger] = None, debug: bool = False) -> float:
        """Wait until next call is allowed according to rate limits.

        Args:
            logger: Optional logger to log rate limiting events
            debug: Whether to enable debug logging for waits

        Returns:
            Time waited in seconds
        """
        with self.lock:
            current_time = time.time()
            elapsed = current_time - self.last_call_time
            wait_time = 0

            if elapsed < self.interval:
                wait_time = self.interval - elapsed
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

    def get_stats(self) -> Dict[str, Any]:
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
        }


class GitHubRateLimiter(RateLimiter):
    """GitHub API-specific rate limiter.

    Extends the base RateLimiter with GitHub-specific functionality.
    """

    def __init__(self, calls_per_minute: int = 30):
        """Initialize GitHub rate limiter.

        Args:
            calls_per_minute: Maximum number of calls allowed per minute
        """
        super().__init__(calls_per_minute=calls_per_minute, name="GitHub")


class LLMRateLimiter(RateLimiter):
    """LLM API-specific rate limiter.

    Extends the base RateLimiter with LLM-specific functionality.
    """

    def __init__(self, calls_per_minute: int = 10):
        """Initialize LLM rate limiter.

        Args:
            calls_per_minute: Maximum number of calls allowed per minute
        """
        super().__init__(calls_per_minute=calls_per_minute, name="LLM")
