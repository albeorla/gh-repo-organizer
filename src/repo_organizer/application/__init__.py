"""Application layer - orchestrates use cases across bounded contexts."""

from .analyze_repositories import analyze_repositories

__all__ = ["analyze_repositories"]
