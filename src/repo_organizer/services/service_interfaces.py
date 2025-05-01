"""Interface definitions for services to enable dependency inversion.

This module contains Protocol classes that define interfaces for various
services used in the application, following the Interface Segregation and
Dependency Inversion principles from SOLID.
"""

from typing import Any, Protocol

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

    def print_summary(self, rate_limiters: list[Any] | None = None) -> None:
        """Print a summary of the run statistics."""
        ...


class RateLimiterProtocol(Protocol):
    """Interface for rate limiter implementations."""

    def wait(
        self,
        logger: LoggerProtocol | None = None,
        debug: bool = False,
    ) -> float:
        """Wait until next call is allowed according to rate limits."""
        ...

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about rate limiting."""
        ...


class GitHubServiceProtocol(Protocol):
    """Interface for GitHub service implementations."""

    def get_repos(self, limit: int = 100) -> list[dict[str, Any]]:
        """Fetch repository information using GitHub CLI."""
        ...

    def get_repo_languages(self, repo_name: str) -> dict[str, float]:
        """Get the language breakdown for a repository."""
        ...

    def get_repo_commits(self, repo_path: str, limit: int = 10) -> list[Commit]:
        """Get recent commits for a repository."""
        ...

    def get_repo_contributors(self, repo_path: str) -> list[Contributor]:
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
        repos: list[dict],
        model_name: str = "claude-3-opus-20240229",
        max_repos: int | None = None,
        retry_failed: bool = False,
        force_repull: bool = False,
    ) -> list[RepoAnalysis]:
        """Analyze multiple GitHub repositories and generate reports."""
        ...
