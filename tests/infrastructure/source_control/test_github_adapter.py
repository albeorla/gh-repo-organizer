"""Tests for the GitHub adapter implementation.
"""

from unittest.mock import MagicMock, patch

import pytest

from repo_organizer.domain.source_control.models import Repository
from repo_organizer.infrastructure.source_control.github_adapter import GitHubAdapter


class TestGitHubAdapter:
    """Test suite for GitHubAdapter."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for tests."""
        settings = MagicMock()
        settings.github_username = "test-user"
        settings.github_token = "test-token"
        settings.github_rate_limit = 30
        return settings

    @pytest.fixture
    def mock_logger(self):
        """Create mock logger for tests."""
        return MagicMock()

    @pytest.fixture
    def mock_rate_limiter(self):
        """Create mock rate limiter for tests."""
        return MagicMock()

    @pytest.fixture
    def github_adapter(self, mock_logger, mock_rate_limiter):
        """Create GitHub adapter instance for tests."""
        with patch("repo_organizer.infrastructure.source_control.github_adapter.GitHubService") as mock_service:
            return GitHubAdapter(
                github_service=mock_service(),
                logger=mock_logger,
                rate_limiter=mock_rate_limiter,
            )

    def test_list_repositories_success(self, github_adapter, mock_logger):
        """Test list_repositories successfully retrieves repositories."""
        # Arrange
        github_adapter.github_service.github_username = "test-user"
        github_adapter.github_service.get_repos.return_value = [
            {
                "name": "repo1",
                "description": "Test repo 1",
                "url": "https://github.com/test-user/repo1",
                "updatedAt": "2025-01-01T00:00:00Z",
                "isArchived": False,
                "stargazerCount": 10,
                "forkCount": 5,
            },
            {
                "name": "repo2",
                "description": "Test repo 2",
                "url": "https://github.com/test-user/repo2",
                "updatedAt": "2025-01-02T00:00:00Z",
                "isArchived": True,
                "stargazerCount": 20,
                "forkCount": 10,
            },
        ]

        # Act
        repos = github_adapter.list_repositories("test-user", limit=10)

        # Assert
        assert len(repos) == 2
        assert isinstance(repos[0], Repository)
        assert repos[0].name == "repo1"
        assert repos[0].description == "Test repo 1"
        assert repos[0].is_archived is False
        assert repos[0].stars == 10
        assert repos[0].forks == 5

        assert repos[1].name == "repo2"
        assert repos[1].is_archived is True
        assert repos[1].stars == 20

        # Verify service call
        github_adapter.github_service.get_repos.assert_called_once_with(limit=10)
        mock_logger.log.assert_called_with(
            "Fetching repositories for test-user", "info",
        )

    def test_list_repositories_wrong_owner(self, github_adapter, mock_logger):
        """Test list_repositories returns empty list for wrong owner."""
        # Arrange
        github_adapter.github_service.github_username = "test-user"

        # Act
        repos = github_adapter.list_repositories("different-user")

        # Assert
        assert len(repos) == 0
        mock_logger.log.assert_any_call(
            "Owner different-user doesn't match configured username test-user",
            "warning",
        )

    def test_list_repositories_exception(self, github_adapter, mock_logger):
        """Test list_repositories handles exceptions gracefully."""
        # Arrange
        github_adapter.github_service.github_username = "test-user"
        github_adapter.github_service.get_repos.side_effect = Exception("API Error")

        # Act
        repos = github_adapter.list_repositories("test-user")

        # Assert
        assert len(repos) == 0
        mock_logger.log.assert_any_call(
            "Error fetching repositories: API Error", "error",
        )

    def test_fetch_languages(self, github_adapter, mock_logger):
        """Test fetch_languages successfully retrieves language breakdown."""
        # Arrange
        repo = Repository(
            name="test-repo",
            description="Test repo",
            url="https://github.com/test-user/test-repo",
            updated_at="2025-01-01T00:00:00Z",
            is_archived=False,
            stars=10,
            forks=5,
        )
        github_adapter.github_service.get_repo_languages.return_value = {
            "Python": 70.5,
            "JavaScript": 20.3,
            "HTML": 9.2,
        }

        # Act
        languages = github_adapter.fetch_languages(repo)

        # Assert
        assert len(languages) == 3
        assert languages[0].language == "Python"
        assert languages[0].percentage == 70.5
        assert languages[1].language == "JavaScript"
        assert languages[1].percentage == 20.3
        assert languages[2].language == "HTML"
        assert languages[2].percentage == 9.2

        # Verify service call
        github_adapter.github_service.get_repo_languages.assert_called_once_with(
            "test-repo",
        )
        mock_logger.log.assert_called_with("Fetching languages for test-repo", "info")

    def test_fetch_languages_exception(self, github_adapter, mock_logger):
        """Test fetch_languages handles exceptions gracefully."""
        # Arrange
        repo = Repository(
            name="test-repo",
            description=None,
            url=None,
            updated_at=None,
            is_archived=False,
            stars=0,
            forks=0,
        )
        github_adapter.github_service.get_repo_languages.side_effect = Exception(
            "API Error",
        )

        # Act
        languages = github_adapter.fetch_languages(repo)

        # Assert
        assert len(languages) == 0
        mock_logger.log.assert_any_call(
            "Error fetching languages for test-repo: API Error", "error",
        )

    def test_recent_commits(self, github_adapter, mock_logger):
        """Test recent_commits handles GitHub API data."""
        # Arrange
        repo = Repository(
            name="test-repo",
            description=None,
            url=None,
            updated_at=None,
            is_archived=False,
            stars=0,
            forks=0,
        )
        github_adapter.github_service.get_repo_commit_activity.return_value = {
            "recent_commits": 5,
            "active_weeks": 3,
            "total_commits": 50,
        }
        github_adapter.github_service.get_repo_contributors_stats.return_value = {
            "contributor_count": 2,
            "active_contributors": 1,
        }

        # Act
        commits = github_adapter.recent_commits(repo, limit=10)

        # Assert
        # We expect an empty list since actual commits require a local clone
        assert len(commits) == 0
        github_adapter.github_service.get_repo_commit_activity.assert_called_once_with(
            "test-repo",
        )
        mock_logger.log.assert_any_call("Fetching recent commits for test-repo", "info")

    def test_contributors(self, github_adapter, mock_logger):
        """Test contributors handles GitHub API data."""
        # Arrange
        repo = Repository(
            name="test-repo",
            description=None,
            url=None,
            updated_at=None,
            is_archived=False,
            stars=0,
            forks=0,
        )
        github_adapter.github_service.get_repo_contributors_stats.return_value = {
            "contributor_count": 2,
            "active_contributors": 1,
        }

        # Act
        contributors = github_adapter.contributors(repo)

        # Assert
        # We expect an empty list since actual contributors require enhanced API access
        assert len(contributors) == 0
        github_adapter.github_service.get_repo_contributors_stats.assert_called_once_with(
            "test-repo",
        )
        mock_logger.log.assert_any_call("Fetching contributors for test-repo", "info")
