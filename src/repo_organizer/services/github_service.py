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
import time
import subprocess
import re
from typing import Any, Dict, List, Optional

import requests
import git
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from repo_organizer.utils.exceptions import APIError
from repo_organizer.utils.logger import Logger
from repo_organizer.utils.rate_limiter import RateLimiter
from repo_organizer.models.repo_models import Commit, Contributor


class GitHubService:
    """Handles interactions with GitHub API and local git repositories.

    This service follows the Repository pattern, providing a unified interface
    for accessing GitHub data from different sources (API and local git).
    """

    def __init__(
        self,
        github_username: str,
        github_token: Optional[str] = None,
        rate_limiter: Optional[RateLimiter] = None,
        logger: Optional[Logger] = None,
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
            self._session.headers.update({"Authorization": f"token {self.github_token}"})

        # GitHub recommends explicitly setting an *application name* in the
        # ``User-Agent`` header so they can reach out in case of issues.
        self._session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "User-Agent": "repo-organizer/1.0 (https://github.com/)",
            }
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(APIError),
    )
    def get_repos(self, limit: int = 100) -> List[Dict[str, Any]]:
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
                    self.logger, debug=getattr(self.logger, "debug_enabled", False)
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
    def get_repo_languages(self, repo_name: str) -> Dict[str, float]:
        """Get the language breakdown for a repository.

        Args:
            repo_name: Name of the repository

        Returns:
            Dictionary mapping language names to percentage of code
        """
        # Apply rate limiting if available
        if self.rate_limiter:
            self.rate_limiter.wait(
                self.logger, debug=getattr(self.logger, "debug_enabled", False)
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
        return {
            lang: (cnt / total_bytes) * 100 for lang, cnt in languages_bytes.items()
        }

    # ------------------------------------------------------------------
    # README extraction helpers
    # ------------------------------------------------------------------

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(APIError),
    )
    def get_repo_readme(self, repo_name: str, max_bytes: int = 5000) -> str:  # noqa: D401
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
                self.logger, debug=getattr(self.logger, "debug_enabled", False)
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

        # ``@retry`` will handle the re-execution in case of APIError.

    def get_repo_commits(self, repo_path: str, limit: int = 10) -> List[Commit]:
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
                            commit.committed_date
                        ).strftime("%Y-%m-%d"),
                    )
                )

            return commits
        except Exception as e:
            if self.logger:
                self.logger.log(
                    f"Error getting commits for {repo_path}: {str(e)}", "warning"
                )
            return []

    def get_repo_contributors(self, repo_path: str) -> List[Contributor]:
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
                                    name=name.strip(), commits=int(count.strip())
                                )
                            )

            return contributors
        except Exception as e:
            if self.logger:
                self.logger.log(
                    f"Error getting contributors for {repo_path}: {str(e)}", "warning"
                )
            return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(APIError),
    )
    def get_repo_issues_stats(self, repo_name: str) -> Dict[str, Any]:
        """Get issue statistics for a repository.

        Args:
            repo_name: Name of the repository

        Returns:
            Dictionary with issue statistics (open_count, closed_count, recent_activity)
        """
        if self.rate_limiter:
            self.rate_limiter.wait(
                self.logger, debug=getattr(self.logger, "debug_enabled", False)
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
                    self.logger.log(f"Error fetching open issues: {open_response.status_code}", "warning")
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
                except:
                    total_open = 0
            
            # Check for recent activity (in the last 30 days)
            recent_activity = False
            if total_open > 0:
                try:
                    recent_params = {"state": "all", "per_page": 5, "sort": "updated", "direction": "desc"}
                    recent_response = self._session.get(open_url, params=recent_params, timeout=15)
                    if recent_response.status_code == 200:
                        recent_issues = recent_response.json()
                        if recent_issues:
                            now = datetime.datetime.now()
                            for issue in recent_issues:
                                updated_at = issue.get("updated_at")
                                if updated_at:
                                    updated_date = datetime.datetime.fromisoformat(updated_at.rstrip("Z"))
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
                if self.rate_limiter:
                    self.rate_limiter.wait(
                        self.logger, debug=getattr(self.logger, "debug_enabled", False)
                    )
                stats_response = self._session.get(stats_url, timeout=15)
                if stats_response.status_code == 200:
                    repo_stats = stats_response.json()
                    # GitHub API provides open_issues_count, but not closed count directly
                    # We can use this as an approximation
                    closed_count = repo_stats.get("open_issues_count", 0) - total_open
                    if closed_count < 0:
                        closed_count = 0
            except Exception as e:
                if self.logger:
                    self.logger.log(f"Error fetching repo stats: {e}", "debug")
            
            return {
                "open_count": total_open,
                "closed_count": closed_count,
                "recent_activity": recent_activity
            }
            
        except Exception as e:
            if self.logger:
                self.logger.log(f"Error fetching issues: {e}", "warning")
            return {"open_count": 0, "closed_count": 0, "recent_activity": False}
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(APIError),
    )
    def get_repo_commit_activity(self, repo_name: str) -> Dict[str, Any]:
        """Get commit activity statistics for a repository.

        Args:
            repo_name: Name of the repository

        Returns:
            Dictionary with commit activity information
        """
        if self.rate_limiter:
            self.rate_limiter.wait(
                self.logger, debug=getattr(self.logger, "debug_enabled", False)
            )

        if self.logger:
            self.logger.log(f"Fetching commit activity for {repo_name}…", "debug")

        url = f"https://api.github.com/repos/{self.github_username}/{repo_name}/commits"
        params = {"per_page": 10}  # Just get recent commits

        try:
            response = self._session.get(url, params=params, timeout=15)
            
            if response.status_code == 404:
                return {"recent_commits": 0, "active_last_month": False, "active_last_year": False}
                
            if response.status_code >= 400:
                if self.logger:
                    self.logger.log(f"Error fetching commits: {response.status_code}", "warning")
                return {"recent_commits": 0, "active_last_month": False, "active_last_year": False}
            
            commits = response.json()
            if not commits:
                return {"recent_commits": 0, "active_last_month": False, "active_last_year": False}
            
            # Check activity periods
            now = datetime.datetime.now()
            active_last_month = False
            active_last_year = False
            
            for commit in commits:
                commit_date_str = commit.get("commit", {}).get("committer", {}).get("date")
                if commit_date_str:
                    commit_date = datetime.datetime.fromisoformat(commit_date_str.rstrip("Z"))
                    days_since = (now - commit_date).days
                    
                    if days_since <= 30:
                        active_last_month = True
                    
                    if days_since <= 365:
                        active_last_year = True
                        
                    if active_last_month and active_last_year:
                        break
            
            return {
                "recent_commits": len(commits),
                "active_last_month": active_last_month,
                "active_last_year": active_last_year
            }
            
        except Exception as e:
            if self.logger:
                self.logger.log(f"Error fetching commit activity: {e}", "warning")
            return {"recent_commits": 0, "active_last_month": False, "active_last_year": False}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(APIError),
    )
    def get_repo_contributors_stats(self, repo_name: str) -> Dict[str, Any]:
        """Get contributor statistics for a repository.

        Args:
            repo_name: Name of the repository

        Returns:
            Dictionary with contributor information
        """
        if self.rate_limiter:
            self.rate_limiter.wait(
                self.logger, debug=getattr(self.logger, "debug_enabled", False)
            )

        if self.logger:
            self.logger.log(f"Fetching contributor stats for {repo_name}…", "debug")

        url = f"https://api.github.com/repos/{self.github_username}/{repo_name}/contributors"
        params = {"per_page": 100}  # Get up to 100 contributors

        try:
            response = self._session.get(url, params=params, timeout=15)
            
            if response.status_code == 404:
                return {"count": 0, "active_contributors": 0}
                
            if response.status_code >= 400:
                if self.logger:
                    self.logger.log(f"Error fetching contributors: {response.status_code}", "warning")
                return {"count": 0, "active_contributors": 0}
            
            contributors = response.json()
            if not contributors:
                return {"count": 0, "active_contributors": 0}
            
            # Count contributors with recent commits
            # This requires checking each contributor's commits which would be too many API calls
            # So we'll just return the total count
            
            return {
                "count": len(contributors),
                "active_contributors": min(len(contributors), 3)  # Rough estimate
            }
            
        except Exception as e:
            if self.logger:
                self.logger.log(f"Error fetching contributors: {e}", "warning")
            return {"count": 0, "active_contributors": 0}
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(APIError),
    )
    def get_repo_dependency_files(self, repo_name: str) -> Dict[str, Any]:
        """Get dependency files for a repository.

        Looks for common dependency files like package.json, requirements.txt, etc.

        Args:
            repo_name: Name of the repository

        Returns:
            Dictionary with dependency information
        """
        if self.rate_limiter:
            self.rate_limiter.wait(
                self.logger, debug=getattr(self.logger, "debug_enabled", False)
            )

        if self.logger:
            self.logger.log(f"Checking for dependency files in {repo_name}…", "debug")

        # Define common dependency file paths for different languages/frameworks
        dependency_files = [
            "package.json",           # Node.js
            "requirements.txt",       # Python
            "Pipfile",                # Python (pipenv)
            "pyproject.toml",         # Python (modern)
            "Gemfile",                # Ruby
            "pom.xml",                # Java (Maven)
            "build.gradle",           # Java (Gradle)
            "composer.json",          # PHP
            "Cargo.toml",             # Rust
            "go.mod",                 # Go
            "*.csproj",               # .NET
        ]
        
        found_files = {}
        content_samples = {}
        
        # Check each file
        for file_path in dependency_files:
            # Skip wildcard files for simplicity
            if "*" in file_path:
                continue
                
            url = f"https://api.github.com/repos/{self.github_username}/{repo_name}/contents/{file_path}"
            
            try:
                if self.rate_limiter:
                    self.rate_limiter.wait(
                        self.logger, debug=getattr(self.logger, "debug_enabled", False)
                    )
                    
                response = self._session.get(url, timeout=15)
                
                if response.status_code == 200:
                    file_info = response.json()
                    
                    # If it's a file (not a directory)
                    if isinstance(file_info, dict) and "type" in file_info and file_info["type"] == "file":
                        found_files[file_path] = True
                        
                        # Try to get content (it's base64 encoded)
                        if "content" in file_info and file_info["encoding"] == "base64":
                            try:
                                content = base64.b64decode(file_info["content"]).decode('utf-8')
                                # Just store a small excerpt to avoid using too much memory
                                content_samples[file_path] = content[:500]
                            except:
                                pass
            except Exception as e:
                if self.logger:
                    self.logger.log(f"Error checking {file_path}: {e}", "debug")
        
        return {
            "has_dependency_files": len(found_files) > 0,
            "dependency_files": list(found_files.keys()),
            "content_samples": content_samples
        }
