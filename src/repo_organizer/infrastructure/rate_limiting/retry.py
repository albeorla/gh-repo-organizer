"""
Retry utility with exponential backoff for API calls.

This module provides a retry decorator that can be used to wrap
API call functions with exponential backoff retry logic.
"""

import time
import random
import functools
from typing import Any, Callable, Optional, Type, List, Union

from repo_organizer.infrastructure.logging.logger import Logger


def retry_with_backoff(
    retries: int = 3,
    backoff_factor: float = 2.0,
    initial_wait: float = 1.0,
    max_wait: float = 60.0,
    exceptions: List[Type[Exception]] = (Exception,),
    logger: Optional[Logger] = None,
    jitter: bool = True,
):
    """Retry decorator with exponential backoff.

    Args:
        retries: Maximum number of retries
        backoff_factor: Factor to multiply wait time by after each failure
        initial_wait: Initial wait time in seconds
        max_wait: Maximum wait time in seconds
        exceptions: List of exceptions to catch and retry on
        logger: Optional logger to log retry events
        jitter: Whether to add randomness to the wait time

    Returns:
        Decorator function
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            wait_time = initial_wait

            for attempt in range(1, retries + 2):  # +2 because we want retries+1 total attempts
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    # Don't retry on the last attempt
                    if attempt > retries:
                        if logger:
                            logger.log(
                                f"Failed after {retries + 1} attempts: {str(e)}",
                                level="error",
                            )
                        raise last_exception
                    
                    # Calculate next wait time with exponential backoff
                    wait_time = min(wait_time * backoff_factor, max_wait)
                    
                    # Add jitter if enabled
                    if jitter:
                        wait_time = wait_time * (0.75 + random.random() * 0.5)
                        
                    if logger:
                        logger.log(
                            f"Retry {attempt}/{retries} after {wait_time:.2f}s due to: {str(e)}",
                            level="warning",
                        )
                        logger.update_stats("retries")
                    
                    time.sleep(wait_time)
            
            # Should never get here, but just in case
            if last_exception:
                raise last_exception
            return None

        return wrapper

    return decorator


class RetryableError(Exception):
    """Base exception class for errors that should trigger a retry."""
    pass


class RateLimitExceededError(RetryableError):
    """Exception raised when an API rate limit is exceeded."""
    pass


class TemporaryAPIError(RetryableError):
    """Exception raised for temporary API errors (e.g., 5xx status codes)."""
    pass


class NetworkError(RetryableError):
    """Exception raised for network connectivity issues."""
    pass


class RetryWithChainedRateLimiters:
    """Context manager for executing code with multiple chained rate limiters.
    
    This context manager allows executing a block of code with multiple
    rate limiters applied in sequence, and with automatic retries on failure.
    
    Example:
        ```python
        with RetryWithChainedRateLimiters(
            [github_limiter, llm_limiter],
            logger=logger,
            retries=3
        ) as retry_ctx:
            # Code to execute with rate limiting
            response = api_client.make_request()
        ```
    """
    
    def __init__(
        self,
        rate_limiters: List[Any],
        logger: Optional[Logger] = None,
        retries: int = 3,
        backoff_factor: float = 2.0,
        initial_wait: float = 1.0,
        max_wait: float = 60.0,
        debug: bool = False,
    ):
        """Initialize the context manager.
        
        Args:
            rate_limiters: List of rate limiters to apply in sequence
            logger: Optional logger to log events
            retries: Maximum number of retries on failure
            backoff_factor: Factor to multiply wait time by after each failure
            initial_wait: Initial wait time in seconds
            max_wait: Maximum wait time in seconds
            debug: Whether to enable debug logging
        """
        self.rate_limiters = rate_limiters
        self.logger = logger
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.initial_wait = initial_wait
        self.max_wait = max_wait
        self.debug = debug
        
    def __enter__(self):
        """Enter the context manager, applying all rate limiters.
        
        Returns:
            Self for context variables
        """
        for limiter in self.rate_limiters:
            limiter.wait(logger=self.logger, debug=self.debug)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager.
        
        Implements automatic retry logic for retryable errors.
        
        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
            
        Returns:
            True if the exception was handled, False otherwise
        """
        if exc_type is None:
            return False
            
        # Only retry for specific exception types
        if not issubclass(exc_type, RetryableError):
            return False
            
        if self.retries <= 0:
            if self.logger:
                self.logger.log(
                    f"No more retries left for: {str(exc_val)}",
                    level="error",
                )
            return False
            
        # Calculate wait time with exponential backoff
        wait_time = min(self.initial_wait * self.backoff_factor, self.max_wait)
        
        # Add jitter
        wait_time = wait_time * (0.75 + random.random() * 0.5)
        
        if self.logger:
            self.logger.log(
                f"Will retry after {wait_time:.2f}s due to: {str(exc_val)}",
                level="warning",
            )
            self.logger.update_stats("retries")
        
        time.sleep(wait_time)
        
        # Decrement retries for next attempt
        self.retries -= 1
        
        # Let the caller know we handled the exception
        return True