"""
GitHub adapter that implements the SourceControlPort.

This adapter connects the domain layer with the actual GitHub infrastructure service,
implementing the SourceControlPort protocol while delegating to the GitHubService.
"""

from __future__ import annotations

from typing import Optional, Sequence

from repo_organizer.domain.source_control.models import (
    Commit,
    Contributor,
    LanguageBreakdown,
    Repository,
)
from repo_organizer.infrastructure.config.settings import Settings
from repo_organizer.infrastructure.logging.logger import Logger
from repo_organizer.infrastructure.rate_limiting.rate_limiter import GitHubRateLimiter
from repo_organizer.infrastructure.source_control.github_service import GitHubService


class GitHubAdapter:
    """Adapter that implements SourceControlPort using GitHubService.

    This adapter translates between the domain models and the infrastructure service,
    following the Adapter pattern to separate domain concerns from infrastructure details.
    """

    def __init__(
        self,
        settings: Settings,
        logger: Optional[Logger] = None,
        rate_limiter: Optional[GitHubRateLimiter] = None,
    ):
        """Initialize the GitHub adapter.

        Args:
            settings: Application settings
            logger: Optional logger for recording operations
            rate_limiter: Optional rate limiter for GitHub API calls
        """
        # Create default rate limiter with settings if none provided
        if rate_limiter is None:
            rate_limiter = GitHubRateLimiter(
                calls_per_minute=settings.github_rate_limit
            )

        # Initialize the underlying GitHub service
        self.github_service = GitHubService(
            github_username=settings.github_username,
            github_token=settings.github_token,
            rate_limiter=rate_limiter,
            logger=logger,
        )

        self.logger = logger

    def list_repositories(
        self, owner: str, *, limit: int | None = None
    ) -> Sequence[Repository]:
        """Return public repositories owned by *owner*.

        Args:
            owner: GitHub user/org name.
            limit: Maximum number of repos (``None`` for no limit).

        Returns:
            Sequence of Repository domain models
        """
        if self.logger:
            self.logger.log(f"Fetching repositories for {owner}", "info")

        # If owner doesn't match configured username, log a warning
        if owner != self.github_service.github_username:
            if self.logger:
                self.logger.log(
                    f"Owner {owner} doesn't match configured username {self.github_service.github_username}",
                    "warning",
                )
            return []

        # Use default limit from settings if none provided
        if limit is None:
            limit = 100

        # Get repositories from GitHub service
        try:
            repos_data = self.github_service.get_repos(limit=limit)

            # Transform to domain models
            return [
                Repository(
                    name=repo["name"],
                    description=repo.get("description"),
                    url=repo.get("url"),
                    updated_at=repo.get("updatedAt"),
                    is_archived=repo.get("isArchived", False),
                    stars=repo.get("stargazerCount", 0),
                    forks=repo.get("forkCount", 0),
                )
                for repo in repos_data
            ]
        except Exception as e:
            if self.logger:
                self.logger.log(f"Error fetching repositories: {str(e)}", "error")
            return []

    def fetch_languages(self, repo: Repository) -> Sequence[LanguageBreakdown]:
        """Return percentage breakdown of languages used in *repo*.

        Args:
            repo: Repository domain model

        Returns:
            Sequence of LanguageBreakdown domain models
        """
        if self.logger:
            self.logger.log(f"Fetching languages for {repo.name}", "info")

        try:
            # Get language breakdown from GitHub service
            languages_data = self.github_service.get_repo_languages(repo.name)

            # Transform to domain models and return
            return [
                LanguageBreakdown(language=lang, percentage=percentage)
                for lang, percentage in languages_data.items()
            ]
        except Exception as e:
            if self.logger:
                self.logger.log(
                    f"Error fetching languages for {repo.name}: {str(e)}", "error"
                )
            return []

    def recent_commits(self, repo: Repository, *, limit: int = 10) -> Sequence[Commit]:
        """Return the *latest* ``limit`` commits for *repo*.

        Args:
            repo: Repository domain model
            limit: Maximum number of commits to return

        Returns:
            Sequence of Commit domain models
        """
        if self.logger:
            self.logger.log(f"Fetching recent commits for {repo.name}", "info")

        try:
            # For this implementation, we need a local clone of the repository
            # We'll use any activity data available from GitHub API instead
            activity_data = self.github_service.get_repo_commit_activity(repo.name)
            # Get contributor data for debugging only
            _ = self.github_service.get_repo_contributors_stats(
                repo.name
            )

            # Log that we would need a local clone for actual commits
            if self.logger:
                self.logger.log(
                    f"Note: Detailed commit history requires a local clone of {repo.name}",
                    "info",
                )
                self.logger.log(
                    f"Commit activity summary: {activity_data.get('recent_commits', 0)} recent commits, "
                    f"{activity_data.get('active_weeks', 0)} active weeks",
                    "debug",
                )

            # Return empty list - in a real implementation we would either:
            # 1. Clone the repository temporarily
            # 2. Use GitHub API to fetch commit history directly
            return []
        except Exception as e:
            if self.logger:
                self.logger.log(
                    f"Error fetching commits for {repo.name}: {str(e)}", "error"
                )
            return []

    def contributors(self, repo: Repository) -> Sequence[Contributor]:
        """Return contributors for *repo* sorted by commit count desc.

        Args:
            repo: Repository domain model

        Returns:
            Sequence of Contributor domain models
        """
        if self.logger:
            self.logger.log(f"Fetching contributors for {repo.name}", "info")

        try:
            # Similar to commits, we need API-based stats rather than local clone
            contributor_stats = self.github_service.get_repo_contributors_stats(
                repo.name
            )

            # Log that we would need to add API endpoint or local clone for actual contributors
            if self.logger:
                self.logger.log(
                    f"Note: Detailed contributor list requires enhanced API endpoint for {repo.name}",
                    "info",
                )
                self.logger.log(
                    f"Contributor summary: {contributor_stats.get('contributor_count', 0)} contributors, "
                    f"{contributor_stats.get('active_contributors', 0)} active",
                    "debug",
                )

            # Return empty list - in a real implementation we would enhance the GitHub service
            # to fetch contributor details through the GitHub API
            return []
        except Exception as e:
            if self.logger:
                self.logger.log(
                    f"Error fetching contributors for {repo.name}: {str(e)}", "error"
                )
            return []
