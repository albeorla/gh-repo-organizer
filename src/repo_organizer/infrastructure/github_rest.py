"""GitHub REST adapter implementing the ``SourceControlPort``.

The class composes (for now *inherits*) the existing ``GitHubService`` to avoid
duplicating logic while the refactor is in progress.  Once all call sites have
migrated to the new port we can clean up the inheritance relationship and use
*pure* composition.
"""

from __future__ import annotations

import base64
from collections.abc import Sequence

import requests

from repo_organizer.domain.source_control.models import (
    Commit,
    Contributor,
    LanguageBreakdown,
    Repository,
)
from repo_organizer.domain.source_control.protocols import SourceControlPort


class GitHubRestAdapter(SourceControlPort):
    """Adapter that fulfils ``SourceControlPort`` using the GitHub REST API."""

    def __init__(
        self,
        github_username: str,
        github_token: str = None,
        rate_limiter=None,
        logger=None,
    ):
        """Initialize the GitHub REST adapter.

        Args:
            github_username: GitHub username
            github_token: GitHub token for authentication
            rate_limiter: Optional rate limiter
            logger: Optional logger
        """
        self.github_username = github_username
        self.github_token = github_token
        self.rate_limiter = rate_limiter
        self.logger = logger

        # Create session for requests
        self._session = requests.Session()
        if github_token:
            self._session.headers.update({"Authorization": f"token {github_token}"})

    # ------------------------------------------------------------------
    # SourceControlPort implementation
    # ------------------------------------------------------------------

    def get_repositories(self, limit: int = 100) -> Sequence[Repository]:
        """Get repositories for the configured user.

        Args:
            limit: Maximum number of repositories to return

        Returns:
            Sequence of Repository domain objects
        """
        if self.logger:
            self.logger.log(
                f"Fetching up to {limit} repositories for {self.github_username}",
            )

        repos = []
        page = 1
        per_page = min(100, limit)  # GitHub maximum per page is 100

        while len(repos) < limit:
            if self.rate_limiter:
                self.rate_limiter.wait(self.logger)

            url = f"https://api.github.com/users/{self.github_username}/repos"
            params = {
                "per_page": per_page,
                "page": page,
                "sort": "updated",
                "direction": "desc",
            }

            response = self._session.get(url, params=params, timeout=15)

            if response.status_code != 200:
                if self.logger:
                    self.logger.log(
                        f"Error fetching repos: {response.status_code} - {response.text}",
                        "error",
                    )
                break

            batch = response.json()
            if not batch:
                break

            for repo_data in batch:
                # Convert to domain model
                repo = Repository(
                    name=repo_data["name"],
                    description=repo_data.get("description"),
                    url=repo_data.get("html_url"),
                    updated_at=repo_data.get("updated_at"),
                    is_archived=repo_data.get("archived", False),
                    stars=repo_data.get("stargazers_count", 0),
                    forks=repo_data.get("forks_count", 0),
                )

                repos.append(repo)

                if len(repos) >= limit:
                    break

            if len(batch) < per_page:
                break

            page += 1

        if self.logger:
            self.logger.log(f"Fetched {len(repos)} repositories")

        return repos

    def get_repository_languages(self, repo_name: str) -> dict[str, float]:
        """Get language breakdown for a repository.

        Args:
            repo_name: Repository name

        Returns:
            Dictionary mapping language names to percentage
        """
        if self.rate_limiter:
            self.rate_limiter.wait(self.logger)

        url = (
            f"https://api.github.com/repos/{self.github_username}/{repo_name}/languages"
        )

        response = self._session.get(url, timeout=15)

        if response.status_code != 200:
            if self.logger:
                self.logger.log(
                    f"Error fetching languages: {response.status_code}", "error",
                )
            return {}

        languages = response.json()

        # Calculate percentages
        total = sum(languages.values())
        if total == 0:
            return {}

        return {
            lang: round((count / total) * 100, 1) for lang, count in languages.items()
        }

    def get_repository_readme(self, repo_name: str) -> str:
        """Get README content for a repository.

        Args:
            repo_name: Repository name

        Returns:
            README content or empty string if not found
        """
        if self.rate_limiter:
            self.rate_limiter.wait(self.logger)

        url = f"https://api.github.com/repos/{self.github_username}/{repo_name}/readme"

        try:
            if self.logger:
                self.logger.log(f"Fetching README for {repo_name}", "info")

            response = self._session.get(url, timeout=15)

            if response.status_code != 200:
                if self.logger:
                    self.logger.log(
                        f"Error fetching README: {response.status_code}", "warning",
                    )
                return ""

            data = response.json()
            content = data.get("content", "")

            if content:
                try:
                    decoded = base64.b64decode(content).decode("utf-8")
                    return decoded
                except Exception as e:
                    if self.logger:
                        self.logger.log(f"Error decoding README: {e}", "error")
                    return ""

            return ""
        except Exception as e:
            if self.logger:
                self.logger.log(f"Error fetching README: {e}", "error")
            return ""

    def list_repositories(
        self, owner: str, *, limit: int | None = None,
    ) -> Sequence[Repository]:
        """List repositories for the given owner.

        Args:
            owner: GitHub username
            limit: Maximum number of repositories to return

        Returns:
            Sequence of Repository domain objects
        """
        # Validate owner matches configured username
        if owner != self.github_username:
            if self.logger:
                self.logger.log(
                    f"Owner mismatch: {owner} != {self.github_username}", "warning",
                )

        # Use the get_repositories method we just implemented
        return self.get_repositories(limit=limit or 100)

    def fetch_languages(self, repo: Repository) -> Sequence[LanguageBreakdown]:
        """Return percentage breakdown of languages used in the repository.

        Args:
            repo: Repository domain object

        Returns:
            Sequence of LanguageBreakdown objects
        """
        # Get languages using the existing method
        lang_percentages = self.get_repository_languages(repo.name)

        # Convert to domain model objects
        return [
            LanguageBreakdown(language=lang, percentage=percentage)
            for lang, percentage in lang_percentages.items()
        ]

    def recent_commits(self, repo: Repository, *, limit: int = 10) -> Sequence[Commit]:
        """Return the latest commits for a repository.

        Args:
            repo: Repository domain object
            limit: Maximum number of commits to return

        Returns:
            Sequence of Commit domain objects
        """
        if self.rate_limiter:
            self.rate_limiter.wait(self.logger)

        url = f"https://api.github.com/repos/{self.github_username}/{repo.name}/commits"
        params = {"per_page": min(100, limit)}

        try:
            response = self._session.get(url, params=params, timeout=15)

            if response.status_code != 200:
                if self.logger:
                    self.logger.log(
                        f"Error fetching commits: {response.status_code}", "warning",
                    )
                return []

            commits_data = response.json()

            commits = []
            for commit_data in commits_data[:limit]:
                commit = Commit(
                    hash=commit_data.get("sha", "")[:7],
                    message=commit_data.get("commit", {})
                    .get("message", "")
                    .split("\n")[0],
                    author=commit_data.get("commit", {})
                    .get("author", {})
                    .get("name", "Unknown"),
                    date=commit_data.get("commit", {})
                    .get("author", {})
                    .get("date", ""),
                )
                commits.append(commit)

            return commits

        except Exception as e:
            if self.logger:
                self.logger.log(f"Error fetching commits for {repo.name}: {e}", "error")
            return []

    def contributors(self, repo: Repository) -> Sequence[Contributor]:
        """Return contributors for a repository sorted by commit count desc.

        Args:
            repo: Repository domain object

        Returns:
            Sequence of Contributor domain objects
        """
        if self.rate_limiter:
            self.rate_limiter.wait(self.logger)

        url = f"https://api.github.com/repos/{self.github_username}/{repo.name}/contributors"
        params = {"per_page": 100}  # Get up to 100 contributors

        try:
            response = self._session.get(url, params=params, timeout=15)

            if response.status_code != 200:
                if self.logger:
                    self.logger.log(
                        f"Error fetching contributors: {response.status_code}",
                        "warning",
                    )
                return []

            contributors_data = response.json()

            contributors = []
            for contributor_data in contributors_data:
                contributor = Contributor(
                    name=contributor_data.get("login", "Unknown"),
                    commits=contributor_data.get("contributions", 0),
                )
                contributors.append(contributor)

            return contributors

        except Exception as e:
            if self.logger:
                self.logger.log(
                    f"Error fetching contributors for {repo.name}: {e}", "error",
                )
            return []
