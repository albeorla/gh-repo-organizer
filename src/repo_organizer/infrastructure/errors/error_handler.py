"""
Error handling utilities.

This module provides utilities for handling errors in a consistent way,
including decorators for error handling and utility functions for error logging.
"""

import functools
import traceback
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, cast

from repo_organizer.infrastructure.errors.exceptions import RepoOrganizerError
from repo_organizer.infrastructure.logging.logger import Logger

# Type variable for callable return type
T = TypeVar("T")


def handle_errors(
    logger: Logger,
    default_message: str = "An error occurred",
    reraise: bool = True,
    handled_exceptions: Optional[List[Type[Exception]]] = None,
    return_value: Any = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for handling errors in a consistent way.
    
    Args:
        logger: Logger instance for error logging
        default_message: Default error message
        reraise: Whether to reraise the exception after handling
        handled_exceptions: List of exception types to handle (defaults to all)
        return_value: Value to return on error (if not reraising)
        
    Returns:
        Decorator function
    """
    if handled_exceptions is None:
        handled_exceptions = [Exception]
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except tuple(handled_exceptions) as e:
                # Get traceback
                tb = traceback.format_exc()
                
                # Build error context
                context = {
                    "function": func.__name__,
                    "args": str(args),
                    "kwargs": str(kwargs),
                    "exception_type": type(e).__name__,
                    "traceback": tb,
                }
                
                # Format error message
                if isinstance(e, RepoOrganizerError):
                    message = e.message
                else:
                    message = str(e) or default_message
                
                # Log the error
                logger.log(
                    f"{default_message}: {message}\n{tb}",
                    level="error",
                )
                
                # Reraise or return the specified value
                if reraise:
                    raise
                return cast(T, return_value)
                
        return wrapper
    
    return decorator


def log_error(
    logger: Logger,
    error: Exception,
    message: str = "An error occurred",
    log_level: str = "error",
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """Log an error with consistent formatting.
    
    Args:
        logger: Logger instance for error logging
        error: Exception to log
        message: Error message prefix
        log_level: Logging level
        context: Additional context for the error
    """
    # Get traceback
    tb = traceback.format_exc()
    
    # Build error context
    error_context = {
        "exception_type": type(error).__name__,
        "traceback": tb,
    }
    
    # Add custom context if provided
    if context:
        error_context.update(context)
    
    # Format error message
    if isinstance(error, RepoOrganizerError):
        error_message = error.message
    else:
        error_message = str(error) or message
    
    # Log the error
    logger.log(
        f"{message}: {error_message}\n{tb}",
        level=log_level,
    )