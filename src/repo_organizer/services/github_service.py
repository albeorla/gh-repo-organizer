"""
GitHub service implementation for fetching repository information.

This module contains the GitHubService class which implements the GitHubServiceProtocol,
providing methods for interacting with GitHub data sources (API and local git repos).
"""

"""GitHub service implementation that relies solely on the public REST API.

The original implementation shell-ed out to the GitHub CLI (``gh``). That
approach required the user to have the CLI installed and authenticated which
is not ideal for portability or headless/server environments.  The service has
been rewritten to use direct HTTPS calls via the official REST endpoints.

Only the interfaces used by the rest of the application were re-implemented
(``get_repos``, ``get_repo_languages`` and ``get_repo_readme``).  The remaining
functions that operate on a *local* repository (e.g. ``get_repo_commits``) are
left untouched as they never depended on the CLI.
"""

from __future__ import annotations

import base64
import datetime
import json
import os
import time
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

        # Validate that the GitHub CLI is available early so the user receives
        # a clear, actionable error instead of a low-level FileNotFoundError
        # later on.
        import shutil

        if shutil.which("gh") is None:
            message = (
                "GitHub CLI ('gh') not found in PATH. Please install it "
                "and authenticate with 'gh auth login' before running the "
                "analyser."
            )
            if self.logger:
                self.logger.log(message, level="error")
            # Raise immediately – continuing without the CLI would break every
            # call anyway.
            raise FileNotFoundError(message)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(APIError),
    )
    def get_repos(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch repository information using GitHub CLI.

        Args:
            limit: Maximum number of repositories to fetch

        Returns:
            List of repository information dictionaries

        Raises:
            APIError: If GitHub CLI command fails
        """
        # Apply rate limiting if available
        if self.rate_limiter:
            self.rate_limiter.wait(
                self.logger, debug=getattr(self.logger, "debug_enabled", False)
            )

        try:
            if self.logger:
                self.logger.log(f"Fetching up to {limit} repositories for user {self.github_username}...")

            # Explicitly specify the owner to ensure we only get the user's repositories
            result = subprocess.run(
                [
                    "gh",
                    "repo",
                    "list",
                    self.github_username,  # Explicitly specify the owner
                    "--limit",
                    str(limit),
                    "--json",
                    "name,description,url,updatedAt,isArchived,stargazerCount,forkCount",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                if self.logger:
                    self.logger.log(f"Error fetching repos: {result.stderr}", "error")
                    self.logger.update_stats("retries")
                raise APIError(f"Error fetching repos: {result.stderr}")

            repos = json.loads(result.stdout)
            if self.logger:
                self.logger.log(
                    f"Successfully fetched {len(repos)} repositories for {self.github_username}", "success"
                )
            return repos
        except subprocess.TimeoutExpired:
            if self.logger:
                self.logger.log("Timeout while fetching repository list", "error")
                self.logger.update_stats("retries")
            raise APIError("Timeout while fetching repository list")
        except json.JSONDecodeError:
            if self.logger:
                self.logger.log("Invalid JSON response from GitHub API", "error")
                self.logger.update_stats("retries")
            raise APIError("Invalid JSON response from GitHub API")
        except Exception as e:
            if self.logger:
                self.logger.log(f"Error fetching repository list: {str(e)}", "error")
            raise APIError(f"Error fetching repository list: {str(e)}")

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

        try:
            if self.logger:
                self.logger.log(f"Fetching languages for {repo_name}...", "debug")

            # Construct the API path - properly handle repository paths
            api_path = f"repos/{self.github_username}/{repo_name}/languages"
            
            result = subprocess.run(
                ["gh", "api", api_path],
                capture_output=True,
                text=True,
                timeout=15,
            )

            if result.returncode != 0:
                if self.logger:
                    self.logger.log(
                        f"Error fetching languages for {repo_name}: {result.stderr}",
                        "warning",
                    )
                    self.logger.update_stats("retries")
                raise APIError(f"Error fetching languages: {result.stderr}")

            if not result.stdout or result.stdout.strip() == "":
                return {}

            try:
                languages = json.loads(result.stdout)
                if languages:
                    # Convert bytes to percentages
                    total = sum(languages.values())
                    return {
                        lang: (value / total) * 100 for lang, value in languages.items()
                    }
            except json.JSONDecodeError:
                if self.logger:
                    self.logger.log(
                        f"Invalid JSON response for languages: {result.stdout[:50]}...",
                        "warning",
                    )
                    self.logger.update_stats("retries")
                raise APIError("Invalid JSON response for languages")

            return {}
        except APIError:
            raise  # Re-raise for retry
        except Exception as e:
            if self.logger:
                self.logger.log(
                    f"Error fetching languages for {repo_name}: {str(e)}", "warning"
                )
            return {}

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

        The GitHub CLI is used to fetch the README in *raw* format which
        avoids the additional step of base-64 decoding the content that the
        REST API normally returns.  The output is truncated to *max_bytes* to
        ensure the prompt does not exceed the model's context window.

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

        try:
            if self.logger:
                self.logger.log(f"Fetching README for {repo_name}…", "debug")

            api_path = f"repos/{self.github_username}/{repo_name}/readme"

            # ``Accept: application/vnd.github.raw`` instructs the API to
            # return the raw file instead of base-64 encoded JSON.
            result = subprocess.run(
                [
                    "gh",
                    "api",
                    "-H",
                    "Accept: application/vnd.github.raw",
                    api_path,
                ],
                capture_output=True,
                text=True,
                timeout=20,
            )

            if result.returncode != 0:
                # README may legitimately be missing – treat 404 as empty.
                if "Not Found" in result.stderr:
                    if self.logger:
                        self.logger.log(
                            f"No README found for {repo_name}", "debug"
                        )
                    return ""

                if self.logger:
                    self.logger.log(
                        f"Error fetching README for {repo_name}: {result.stderr}",
                        "warning",
                    )
                    self.logger.update_stats("retries")
                raise APIError(result.stderr.strip())

            # Truncate to *max_bytes* characters to stay within context limits
            readme_content = (result.stdout or "")[:max_bytes]

            # Collapse excessive whitespace that does not add much signal to
            # the model while still preserving separate paragraphs.
            readme_content = "\n".join(
                [line.rstrip() for line in readme_content.splitlines()]
            )

            return readme_content

        except APIError:
            raise
        except subprocess.TimeoutExpired:
            if self.logger:
                self.logger.log(
                    f"Timeout while fetching README for {repo_name}", "warning"
                )
            raise APIError("Timeout while fetching README")
        except Exception as e:
            if self.logger:
                self.logger.log(
                    f"Unexpected error fetching README for {repo_name}: {str(e)}",
                    "warning",
                )
            return ""

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
