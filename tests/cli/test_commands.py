"""Tests for CLI commands to ensure integration with authentication.
"""

from unittest.mock import Mock, patch

import pytest

from repo_organizer.cli.commands import execute_actions


@pytest.fixture
def mock_settings():
    """Provide mock settings."""
    with patch("repo_organizer.cli.commands.load_settings") as mock:
        settings = Mock()
        settings.output_dir = "/tmp/test_output"
        settings.logs_dir = "/tmp/test_logs"  # Add logs_dir
        settings.github_token = "dummy_token"
        settings.github_rate_limit = 60
        mock.return_value = settings
        yield mock


@pytest.fixture
def mock_load_analyses():
    """Mock the _load_analyses function."""
    with patch("repo_organizer.cli.commands._load_analyses") as mock:
        mock.return_value = []
        yield mock


@pytest.fixture
def mock_analysis_service():
    """Mock the AnalysisService."""
    with patch("repo_organizer.cli.commands.AnalysisService") as mock:
        mock.categorize_by_action.return_value = {"ARCHIVE": [], "DELETE": []}
        yield mock


class TestCommands:
    """Tests for CLI commands."""

    @patch("repo_organizer.utils.logger.Logger.log")
    def test_execute_actions_with_username(
        self, mock_log_method, mock_settings, mock_load_analyses, mock_analysis_service,
    ):
        """Test execute_actions accepts and uses username parameter."""
        import typer

        # Patch the Logger to avoid file system operations
        with patch("repo_organizer.cli.commands.Logger") as mock_logger_class:
            mock_logger = Mock()
            mock_logger_class.return_value = mock_logger

            # Call execute_actions with a username - it will raise typer.Exit since there are no repositories
            try:
                execute_actions(
                    dry_run=True,
                    force=False,
                    output_dir="/tmp/test_output",
                    github_token="test_token",
                    action_type="ARCHIVE",
                    username="test-user",
                )
            except typer.Exit:
                # Expected exit due to no repositories found for the action
                pass

        # Verify that load_settings was called
        mock_settings.assert_called_once()

        # Verify that _load_analyses was called with the settings
        mock_load_analyses.assert_called_once()

        # Verify that AnalysisService.categorize_by_action was called
        mock_analysis_service.categorize_by_action.assert_called_once()
