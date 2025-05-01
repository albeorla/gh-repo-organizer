"""Source Control Infrastructure Layer.

This module contains implementations for source control adapters.
Primarily focused on GitHub integration and repository management.
"""

# Import implementations that should be accessible from this package
from .github_adapter import GitHubAdapter

__all__ = [
    "GitHubAdapter",
]
