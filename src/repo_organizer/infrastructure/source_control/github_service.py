"""GitHub service implementation that relies solely on the public REST API.

The original implementation shell-ed out to the GitHub CLI (``gh``). That
approach required the user to have the CLI installed and authenticated which
is not ideal for portability or headless/server environments.  The service has
therefore been rewritten to use direct HTTPS calls via the official REST
endpoints.  Only the interfaces used by the rest of the application were
re-implemented (``get_repos``, ``get_repo_languages`` and ``get_repo_readme``).
The remaining functions that operate on a *local* repository (e.g.
``get_repo_commits``) never depended on the CLI and therefore remain
unchanged.
"""

from __future__ import annotations

import base64
import datetime
import json
import os
import re
import subprocess
from typing import TYPE_CHECKING, Any

import git
import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from repo_organizer.infrastructure.analysis.pydantic_models import Commit, Contributor
from repo_organizer.utils.exceptions import APIError

if TYPE_CHECKING:
    from repo_organizer.utils.logger import Logger
    from repo_organizer.utils.rate_limiter import RateLimiter


class GitHubService:
    """Handles interactions with GitHub API and local git repositories.

    This service follows the Repository pattern, providing a unified interface
    for accessing GitHub data from different sources (API and local git).
    """

    def __init__(
        self,
        github_username: str,
        github_token: str | None = None,
        rate_limiter: RateLimiter | None = None,
        logger: Logger | None = None,
    ):
        """Initialize the GitHub service.

        Args:
            github_username: GitHub username
            github_token: Optional GitHub token for API access
            rate_limiter: Optional rate limiter for API calls
            logger: Optional logger for service operations
        """
        self.github_username = github_username
        self.github_token = github_token
        self.rate_limiter = rate_limiter
        self.logger = logger

        # ------------------------------------------------------------------
        # Session set-up
        # ------------------------------------------------------------------
        # Use a *single* ``requests.Session`` instance for the lifetime of the
        # service.  This drastically reduces the overhead of establishing TLS
        # hand-shakes and negotiating HTTP/2 on every request.

        self._session = requests.Session()

        # Inject the *optional* GitHub token into every request.
        if self.github_token:
            self._session.headers.update(
                {"Authorization": f"token {self.github_token}"},
            )

        # GitHub recommends explicitly setting an *application name* in the
        # ``User-Agent`` header so they can reach out in case of issues.
        self._session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "User-Agent": "repo-organizer/1.0 (https://github.com/)",
            },
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(APIError),
    )
    def get_repos(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return public (non-fork) repositories for *github_username*.

        The GitHub REST API limits the ``per_page`` parameter to 100 items.
        Pagination is therefore required when *limit* exceeds that value.

        Args:
            limit: Maximum number of repositories to fetch (defaults to 100).

        Raises:
            APIError: On network failures or unexpected status codes.
        """
        collected: list[dict[str, Any]] = []
        page = 1

        while len(collected) < limit:
            # ------------------------------------------------------------------
            # Respect API rate limits *before* performing the request.
            # ------------------------------------------------------------------
            if self.rate_limiter:
                self.rate_limiter.wait(
                    self.logger,
                    debug=getattr(self.logger, "debug_enabled", False),
                )

            params: dict[str, Any] = {
                "per_page": min(100, limit - len(collected)),
                "page": page,
                "type": "owner",  # Only repos the user owns (exclude forks)
                "sort": "updated",
            }

            url = f"https://api.github.com/users/{self.github_username}/repos"

            try:
                response = self._session.get(url, params=params, timeout=30)
            except Exception as exc:  # pragma: no cover – network errors
                if self.logger:
                    self.logger.log(f"Network error fetching repos: {exc}", "error")
                raise APIError(str(exc)) from exc

            if response.status_code >= 400:
                if self.logger:
                    self.logger.log(
                        f"GitHub API error ({response.status_code}) while fetching repos: {response.text}",
                        "error",
                    )
                    # Count *all* 4xx/5xx responses as retries – they are
                    # potentially transient (e.g. 502/503) or can be retried
                    # after back-off (e.g. 403 rate limited without token).
                    self.logger.update_stats("retries")
                raise APIError(f"GitHub API responded with {response.status_code}")

            try:
                data = response.json()
            except json.JSONDecodeError as exc:  # pragma: no cover
                if self.logger:
                    self.logger.log("Invalid JSON when fetching repos", "error")
                    self.logger.update_stats("retries")
                raise APIError("Invalid JSON when fetching repos") from exc

            # ``type: owner`` already filters forks, but be defensive in case
            # that behaviour changes.
            collected.extend([repo for repo in data if not repo.get("fork", False)])

            if len(data) < params["per_page"]:  # No more pages
                break

            page += 1

        # Map GitHub REST response field names to the camel-cased keys used by
        # the rest of the application to avoid touching dozens of call sites.
        def _transform(repo: dict[str, Any]) -> dict[str, Any]:
            return {
                "name": repo.get("name"),
                "description": repo.get("description"),
                "url": repo.get("html_url"),
                "updatedAt": repo.get("updated_at"),
                "isArchived": repo.get("archived", False),
                "stargazerCount": repo.get("stargazers_count", 0),
                "forkCount": repo.get("forks_count", 0),
            }

        results = [_transform(r) for r in collected[:limit]]

        if self.logger:
            self.logger.log(
                f"Successfully fetched {len(results)} repositories for {self.github_username}",
                "success",
            )

        return results

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(APIError),
    )
    def get_repo_languages(self, repo_name: str) -> dict[str, float]:
        """Get the language breakdown for a repository.

        Args:
            repo_name: Name of the repository

        Returns:
            Dictionary mapping language names to percentage of code
        """
        # Apply rate limiting if available
        if self.rate_limiter:
            self.rate_limiter.wait(
                self.logger,
                debug=getattr(self.logger, "debug_enabled", False),
            )

        if self.logger:
            self.logger.log(f"Fetching languages for {repo_name}…", "debug")

        url = f"https://api.github.com/repos/{self.github_username}/{repo_name}/languages"

        try:
            response = self._session.get(url, timeout=15)
        except Exception as exc:  # pragma: no cover
            if self.logger:
                self.logger.log(
                    f"Network error fetching languages for {repo_name}: {exc}",
                    "warning",
                )
            raise APIError(str(exc)) from exc

        if response.status_code == 404:
            # Repository deleted or made private – treat as empty
            return {}

        if response.status_code >= 400:
            if self.logger:
                self.logger.log(
                    f"GitHub API error ({response.status_code}) fetching languages for {repo_name}",
                    "warning",
                )
                self.logger.update_stats("retries")
            raise APIError("Error fetching languages")

        try:
            languages_bytes = response.json()
        except json.JSONDecodeError as exc:  # pragma: no cover
            if self.logger:
                self.logger.log("Invalid JSON response for languages", "warning")
            raise APIError("Invalid JSON response for languages") from exc

        if not languages_bytes:
            return {}

        total_bytes = sum(languages_bytes.values()) or 1  # avoid ZeroDivision
        return {lang: (cnt / total_bytes) * 100 for lang, cnt in languages_bytes.items()}

    # ------------------------------------------------------------------
    # README extraction helpers
    # ------------------------------------------------------------------

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(APIError),
    )
    def get_repo_readme(self, repo_name: str, max_bytes: int = 5000) -> str:
        """Return the raw README contents for *repo_name*.

        The GitHub REST API is queried with an ``Accept: application/vnd.github.raw``
        header so the server returns the file content *directly* without the
        base-64 encoding used by the default representation.  The response is
        truncated to *max_bytes* characters to ensure we stay within the
        language-model's context window.

        Args:
            repo_name: Name of the repository.
            max_bytes: Maximum number of bytes to return (defaults to 5 000).

        Returns:
            A UTF-8 string containing up to *max_bytes* characters of the
            repository's README.  Returns an empty string when the README is
            missing or cannot be retrieved.
        """
        if self.rate_limiter:
            self.rate_limiter.wait(
                self.logger,
                debug=getattr(self.logger, "debug_enabled", False),
            )

        if self.logger:
            self.logger.log(f"Fetching README for {repo_name}…", "debug")

        url = f"https://api.github.com/repos/{self.github_username}/{repo_name}/readme"

        headers = {"Accept": "application/vnd.github.raw"}

        try:
            response = self._session.get(url, headers=headers, timeout=20)
        except Exception as exc:  # pragma: no cover
            if self.logger:
                self.logger.log(
                    f"Network error fetching README for {repo_name}: {exc}",
                    "warning",
                )
            raise APIError(str(exc)) from exc

        if response.status_code == 404:
            # README may legitimately be missing – treat 404 as empty.
            if self.logger:
                self.logger.log(f"No README found for {repo_name}", "debug")
            return ""

        if response.status_code >= 400:
            if self.logger:
                self.logger.log(
                    f"GitHub API error ({response.status_code}) fetching README for {repo_name}",
                    "warning",
                )
                self.logger.update_stats("retries")
            raise APIError("Error fetching README")

        # Truncate to *max_bytes* characters to stay within context limits.
        readme_content = (response.text or "")[:max_bytes]

        # Collapse excessive whitespace that does not add much signal to the
        # language model while still preserving separate paragraphs.
        readme_content = "\n".join(line.rstrip() for line in readme_content.splitlines())

        return readme_content

    def get_repo_commits(self, repo_path: str, limit: int = 10) -> list[Commit]:
        """Get recent commits for a repository.

        Args:
            repo_path: Local path to the repository
            limit: Maximum number of commits to retrieve

        Returns:
            List of Commit objects
        """
        try:
            if not os.path.isdir(repo_path):
                return []

            repo = git.Repo(repo_path)
            commits = []

            for commit in list(repo.iter_commits("HEAD", max_count=limit)):
                commits.append(
                    Commit(
                        hash=commit.hexsha[:7],
                        message=commit.message.split("\n")[0],
                        author=commit.author.name,
                        date=datetime.datetime.fromtimestamp(
                            commit.committed_date,
                        ).strftime("%Y-%m-%d"),
                    ),
                )

            return commits
        except Exception as e:
            if self.logger:
                self.logger.log(
                    f"Error getting commits for {repo_path}: {e!s}",
                    "warning",
                )
            return []

    def get_repo_contributors(self, repo_path: str) -> list[Contributor]:
        """Get contributors for a repository.

        Args:
            repo_path: Local path to the repository

        Returns:
            List of Contributor objects
        """
        try:
            if not os.path.isdir(repo_path):
                return []

            result = subprocess.run(
                ["git", "shortlog", "-sn", "--no-merges"],
                capture_output=True,
                text=True,
                cwd=repo_path,
                check=False,
            )

            contributors = []
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if line.strip():
                        parts = line.strip().split("\t")
                        if len(parts) == 2:
                            count, name = parts
                            contributors.append(
                                Contributor(
                                    name=name.strip(),
                                    commits=int(count.strip()),
                                ),
                            )

            return contributors
        except Exception as e:
            if self.logger:
                self.logger.log(
                    f"Error getting contributors for {repo_path}: {e!s}",
                    "warning",
                )
            return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(APIError),
    )
    def get_repo_issues_stats(self, repo_name: str) -> dict[str, Any]:
        """Get issue statistics for a repository.

        Args:
            repo_name: Name of the repository

        Returns:
            Dictionary with issue statistics (open_count, closed_count, recent_activity)
        """
        if self.rate_limiter:
            self.rate_limiter.wait(
                self.logger,
                debug=getattr(self.logger, "debug_enabled", False),
            )

        if self.logger:
            self.logger.log(f"Fetching issues for {repo_name}…", "debug")

        # Get open issues count
        open_url = f"https://api.github.com/repos/{self.github_username}/{repo_name}/issues"
        params = {"state": "open", "per_page": 1}

        try:
            open_response = self._session.get(open_url, params=params, timeout=15)

            if open_response.status_code == 404:
                return {"open_count": 0, "closed_count": 0, "recent_activity": False}

            if open_response.status_code >= 400:
                if self.logger:
                    self.logger.log(
                        f"Error fetching open issues: {open_response.status_code}",
                        "warning",
                    )
                return {"open_count": 0, "closed_count": 0, "recent_activity": False}

            # Get total from Link header or fallback to counting
            total_open = 0
            if "Link" in open_response.headers:
                link_header = open_response.headers["Link"]
                last_match = re.search(r'page=(\d+)>; rel="last"', link_header)
                if last_match:
                    total_open = int(last_match.group(1))

            if total_open == 0:
                try:
                    # Just count what we got
                    total_open = len(open_response.json())
                except Exception:  # Handle any JSON decode or other errors
                    total_open = 0

            # Check for recent activity (in the last 30 days)
            recent_activity = False
            if total_open > 0:
                try:
                    recent_params = {
                        "state": "all",
                        "per_page": 5,
                        "sort": "updated",
                        "direction": "desc",
                    }
                    recent_response = self._session.get(
                        open_url,
                        params=recent_params,
                        timeout=15,
                    )
                    if recent_response.status_code == 200:
                        recent_issues = recent_response.json()
                        if recent_issues:
                            now = datetime.datetime.now()
                            for issue in recent_issues:
                                updated_at = issue.get("updated_at")
                                if updated_at:
                                    updated_date = datetime.datetime.fromisoformat(
                                        updated_at.rstrip("Z"),
                                    )
                                    if (now - updated_date).days <= 30:
                                        recent_activity = True
                                        break
                except Exception as e:
                    if self.logger:
                        self.logger.log(f"Error checking recent activity: {e}", "debug")

            # Get closed issues count - approximate using repo stats
            closed_count = 0
            stats_url = f"https://api.github.com/repos/{self.github_username}/{repo_name}"

            try:
                stats_response = self._session.get(stats_url, timeout=15)
                if stats_response.status_code == 200:
                    repo_data = stats_response.json()
                    total_issues = repo_data.get("open_issues_count", 0)
                    # Total issues count in GitHub API includes PRs, so it's an approximation
                    # but we know open_issues_count includes PRs, so closed issues estimate is rough
                    if total_issues >= total_open:
                        closed_count = max(0, total_issues - total_open)
            except Exception as e:
                if self.logger:
                    self.logger.log(f"Error fetching repo stats: {e}", "debug")

            return {
                "open_count": total_open,
                "closed_count": closed_count,
                "recent_activity": recent_activity,
            }
        except Exception as e:
            if self.logger:
                self.logger.log(f"Error fetching issues stats: {e!s}", "warning")
                self.logger.update_stats("retries")
            raise APIError(f"Error fetching issues stats: {e!s}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(APIError),
    )
    def get_repo_commit_activity(self, repo_name: str) -> dict[str, Any]:
        """Get commit activity statistics for a repository.

        Args:
            repo_name: Name of the repository

        Returns:
            Dictionary with commit activity statistics
        """
        if self.rate_limiter:
            self.rate_limiter.wait(
                self.logger,
                debug=getattr(self.logger, "debug_enabled", False),
            )

        if self.logger:
            self.logger.log(f"Fetching commit activity for {repo_name}…", "debug")

        url = (
            f"https://api.github.com/repos/{self.github_username}/{repo_name}/stats/commit_activity"
        )

        try:
            response = self._session.get(url, timeout=20)

            if response.status_code == 202:
                # GitHub is computing the stats asynchronously
                if self.logger:
                    self.logger.log(
                        f"GitHub is computing commit stats for {repo_name}, retrying...",
                        "debug",
                    )
                # This will trigger a retry through the decorator
                raise APIError("GitHub is computing stats, retry needed")

            if response.status_code == 204 or response.status_code == 404:
                return {"recent_commits": 0, "active_weeks": 0, "total_commits": 0}

            if response.status_code >= 400:
                if self.logger:
                    self.logger.log(
                        f"Error fetching commit activity: {response.status_code}",
                        "warning",
                    )
                return {"recent_commits": 0, "active_weeks": 0, "total_commits": 0}

            try:
                activity_data = response.json()
            except json.JSONDecodeError:
                return {"recent_commits": 0, "active_weeks": 0, "total_commits": 0}

            # Process the weekly commit data (last 52 weeks)
            total_commits = 0
            active_weeks = 0
            recent_commits = 0  # Last 4 weeks

            if isinstance(activity_data, list):
                weeks_to_consider = min(len(activity_data), 52)
                for i in range(weeks_to_consider):
                    week_data = activity_data[i]
                    week_commits = week_data.get("total", 0)
                    total_commits += week_commits
                    if week_commits > 0:
                        active_weeks += 1

                    # Count recent commits (last 4 weeks)
                    if i < 4:  # Most recent 4 weeks
                        recent_commits += week_commits

            return {
                "recent_commits": recent_commits,
                "active_weeks": active_weeks,
                "total_commits": total_commits,
            }
        except Exception as e:
            if self.logger:
                self.logger.log(f"Error fetching commit activity: {e!s}", "warning")
                self.logger.update_stats("retries")
            raise APIError(f"Error fetching commit activity: {e!s}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(APIError),
    )
    def get_repo_contributors_stats(self, repo_name: str) -> dict[str, Any]:
        """Get contributor statistics for a repository.

        Args:
            repo_name: Name of the repository

        Returns:
            Dictionary with contributor statistics
        """
        if self.rate_limiter:
            self.rate_limiter.wait(
                self.logger,
                debug=getattr(self.logger, "debug_enabled", False),
            )

        if self.logger:
            self.logger.log(f"Fetching contributor stats for {repo_name}…", "debug")

        url = f"https://api.github.com/repos/{self.github_username}/{repo_name}/stats/contributors"

        try:
            response = self._session.get(url, timeout=20)

            if response.status_code == 202:
                # GitHub is computing the stats asynchronously
                if self.logger:
                    self.logger.log(
                        f"GitHub is computing contributor stats for {repo_name}, retrying...",
                        "debug",
                    )
                # This will trigger a retry through the decorator
                raise APIError("GitHub is computing stats, retry needed")

            if response.status_code == 204 or response.status_code == 404:
                return {"contributor_count": 0, "active_contributors": 0}

            if response.status_code >= 400:
                if self.logger:
                    self.logger.log(
                        f"Error fetching contributor stats: {response.status_code}",
                        "warning",
                    )
                return {"contributor_count": 0, "active_contributors": 0}

            try:
                contributors_data = response.json()
            except json.JSONDecodeError:
                return {"contributor_count": 0, "active_contributors": 0}

            # Process the contributor data
            contributor_count = len(contributors_data) if isinstance(contributors_data, list) else 0
            active_contributors = 0

            # Count contributors with activity in the last 3 months
            if isinstance(contributors_data, list):
                for contributor in contributors_data:
                    weeks = contributor.get("weeks", [])
                    if isinstance(weeks, list) and len(weeks) >= 12:  # Last ~3 months
                        recent_commits = sum(week.get("c", 0) for week in weeks[-12:])
                        if recent_commits > 0:
                            active_contributors += 1

            return {
                "contributor_count": contributor_count,
                "active_contributors": active_contributors,
            }
        except Exception as e:
            if self.logger:
                self.logger.log(
                    f"Error fetching contributor stats: {e!s}",
                    "warning",
                )
                self.logger.update_stats("retries")
            raise APIError(f"Error fetching contributor stats: {e!s}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(APIError),
    )
    def get_repo_dependency_files(self, repo_name: str) -> dict[str, Any]:
        """Get dependency files for a repository (package.json, requirements.txt, etc).

        Args:
            repo_name: Name of the repository

        Returns:
            Dictionary with dependency file contents
        """
        if self.rate_limiter:
            self.rate_limiter.wait(
                self.logger,
                debug=getattr(self.logger, "debug_enabled", False),
            )

        if self.logger:
            self.logger.log(f"Fetching dependency files for {repo_name}…", "debug")

        # Common dependency file paths
        dep_files = [
            "package.json",  # Node.js
            "requirements.txt",  # Python
            "Pipfile",  # Python (pipenv)
            "pyproject.toml",  # Python (modern)
            "Gemfile",  # Ruby
            "pom.xml",  # Java (Maven)
            "build.gradle",  # Java (Gradle)
            "composer.json",  # PHP
            "go.mod",  # Go
            "Cargo.toml",  # Rust
        ]

        results = {}
        found_any = False

        for file_path in dep_files:
            url = f"https://api.github.com/repos/{self.github_username}/{repo_name}/contents/{file_path}"

            try:
                response = self._session.get(url, timeout=15)

                if response.status_code == 200:
                    try:
                        content_data = response.json()
                        if content_data.get("type") == "file":
                            # File exists, get content
                            content = base64.b64decode(
                                content_data.get("content", ""),
                            ).decode("utf-8")
                            results[file_path] = content
                            found_any = True
                    except Exception as e:
                        if self.logger:
                            self.logger.log(
                                f"Error parsing {file_path} content: {e}",
                                "debug",
                            )
            except Exception as e:
                if self.logger:
                    self.logger.log(f"Error fetching {file_path}: {e!s}", "debug")

        # Add a summary if any files were found
        if found_any:
            summary = []
            for file, content in results.items():
                if file == "package.json":
                    try:
                        data = json.loads(content)
                        deps = list(data.get("dependencies", {}).keys())
                        dev_deps = list(data.get("devDependencies", {}).keys())
                        summary.append(
                            f"Node.js project with {len(deps)} dependencies and {len(dev_deps)} dev dependencies",
                        )
                    except Exception:
                        summary.append("Node.js project (could not parse package.json)")
                elif file == "requirements.txt":
                    lines = [
                        line
                        for line in content.splitlines()
                        if line.strip() and not line.startswith("#")
                    ]
                    summary.append(f"Python project with {len(lines)} dependencies")
                elif file == "pyproject.toml":
                    summary.append(
                        "Python project using modern tooling (pyproject.toml)",
                    )
                elif file == "go.mod":
                    summary.append("Go module")
                elif file == "Cargo.toml":
                    summary.append("Rust project")
                else:
                    summary.append(f"Found dependency file: {file}")

            results["summary"] = ", ".join(summary)

        return results
