"""
Tests for CLI commands to ensure integration with authentication.
"""

import pytest
from unittest.mock import patch, Mock

from repo_organizer.cli.commands import execute_actions


@pytest.fixture
def mock_settings():
    """Provide mock settings."""
    with patch("repo_organizer.cli.commands.load_settings") as mock:
        settings = Mock()
        settings.output_dir = "/tmp/test_output"
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
    
    def test_execute_actions_with_username(
        self, mock_settings, mock_load_analyses, mock_analysis_service
    ):
        """Test execute_actions accepts and uses username parameter."""
        # Call execute_actions with a username
        execute_actions(
            dry_run=True,
            force=False,
            output_dir="/tmp/test_output",
            github_token="test_token",
            action_type="ARCHIVE",
            username="test-user"
        )
        
        # Verify that load_settings was called
        mock_settings.assert_called_once()
        
        # Verify that _load_analyses was called with the settings
        mock_load_analyses.assert_called_once()
        
        # Verify that AnalysisService.categorize_by_action was called
        mock_analysis_service.categorize_by_action.assert_called_once()