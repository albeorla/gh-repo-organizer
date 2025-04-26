"""
Legacy models package for backward compatibility.

This package re-exports the models from the infrastructure layer to maintain
backward compatibility with code that imports from the old location.

DEPRECATED: New code should import directly from infrastructure.analysis.pydantic_models.
"""

# Re-export models for backward compatibility
from repo_organizer.infrastructure.analysis.pydantic_models import (
    LanguageBreakdown,
    RepoRecommendation,
    RepoAnalysis,
    RepoInfo,
    Commit,
    Contributor,
)

__all__ = [
    "LanguageBreakdown",
    "RepoRecommendation",
    "RepoAnalysis",
    "RepoInfo",
    "Commit",
    "Contributor",
]
