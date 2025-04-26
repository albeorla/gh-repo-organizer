"""
Interface definitions for services to enable dependency inversion.

This module contains Protocol classes that define interfaces for various
services used in the application, following the Interface Segregation and
Dependency Inversion principles from SOLID.
"""

from typing import Protocol, List, Dict, Any, Optional
from repo_organizer.infrastructure.analysis.pydantic_models import (
    Commit,
    Contributor,
    RepoAnalysis,
)


class LoggerProtocol(Protocol):
    """Interface for logger implementations."""

    def log(self, message: str, level: str = "info") -> None:
        """Log a message at the specified level."""
        ...

    def update_stats(self, key: str, value: Any = 1, increment: bool = True) -> None:
        """Update statistics."""
        ...

    def print_summary(self, rate_limiters: Optional[List[Any]] = None) -> None:
        """Print a summary of the run statistics."""
        ...


class RateLimiterProtocol(Protocol):
    """Interface for rate limiter implementations."""

    def wait(
        self, logger: Optional[LoggerProtocol] = None, debug: bool = False
    ) -> float:
        """Wait until next call is allowed according to rate limits."""
        ...

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about rate limiting."""
        ...


class GitHubServiceProtocol(Protocol):
    """Interface for GitHub service implementations."""

    def get_repos(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch repository information using GitHub CLI."""
        ...

    def get_repo_languages(self, repo_name: str) -> Dict[str, float]:
        """Get the language breakdown for a repository."""
        ...

    def get_repo_commits(self, repo_path: str, limit: int = 10) -> List[Commit]:
        """Get recent commits for a repository."""
        ...

    def get_repo_contributors(self, repo_path: str) -> List[Contributor]:
        """Get contributors for a repository."""
        ...


class LLMServiceProtocol(Protocol):
    """Interface for language model service implementations."""

    def create_analysis_chain(self) -> Any:
        """Create a runnable chain for repository analysis."""
        ...


class RepositoryAnalyzerServiceProtocol(Protocol):
    """Interface for repository analyzer service implementations."""

    def run(self) -> None:
        """Run the repository analysis."""
        ...

    def analyze_repos(
        self,
        repos: List[Dict],
        model_name: str = "claude-3-opus-20240229",
        max_repos: Optional[int] = None,
        retry_failed: bool = False,
        force_repull: bool = False,
    ) -> List[RepoAnalysis]:
        """Analyze multiple GitHub repositories and generate reports."""
        ...
