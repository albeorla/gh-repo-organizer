"""Shared kernel utilities and abstractions.

This package groups *cross-cutting* concerns that are used across multiple
bounded contexts (logging, rate limiting, common exceptions, etc.).  Having
them in a dedicated package prevents vicious import cycles and clarifies that
these utilities do **not** belong to any specific domain.

The initial implementation re-exports the existing classes living under
``repo_organizer.utils`` so that the legacy modules keep working unchanged.  In
subsequent refactor stages we can progressively move the actual
implementations into this package without breaking imports.
"""

# NOTE:  Re-export legacy utilities so existing code keeps working while we
# gradually migrate call-sites to the new import paths.

from repo_organizer.utils.logger import Logger as Logger  # noqa: F401
from repo_organizer.utils.rate_limiter import RateLimiter as RateLimiter  # noqa: F401
from repo_organizer.utils.exceptions import APIError  # noqa: F401


__all__ = [
    "Logger",
    "RateLimiter",
    "APIError",
]
