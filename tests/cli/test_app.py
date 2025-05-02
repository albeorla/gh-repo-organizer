"""Tests for the main CLI application and command groups."""

from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from repo_organizer.cli.app import app
from repo_organizer.cli.commands.actions import actions_app
from repo_organizer.cli.commands.logs import logs_app
from repo_organizer.cli.commands.repo import repo_app
from repo_organizer.cli.commands.reports import reports_app

runner = CliRunner()


@pytest.fixture
def mock_settings():
    """Provide mock settings."""
    with patch("repo_organizer.infrastructure.config.settings.load_settings") as mock:
        settings = Mock()
        settings.output_dir = "/tmp/test_output"
        settings.logs_dir = "/tmp/test_logs"
        settings.github_token = "dummy_token"
        settings.github_rate_limit = 60
        settings.github_username = "test-user"
        mock.return_value = settings
        yield mock


@pytest.fixture
def mock_console():
    """Mock rich console to avoid terminal output."""
    with patch("rich.console.Console.print") as mock:
        yield mock


def test_version_command():
    """Test the --version flag shows version information."""
    with patch("repo_organizer.__version__", "0.1.0"):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.stdout


def test_help_command():
    """Test the --help flag shows command groups."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "repo" in result.stdout
    assert "reports" in result.stdout
    assert "logs" in result.stdout
    assert "actions" in result.stdout
    assert "dev" in result.stdout


def test_completion_command_auto_detect(mock_console):
    """Test the completion command with auto-detection."""
    with patch("shellingham.detect_shell", return_value=("zsh", "/bin/zsh")):
        result = runner.invoke(app, ["completion"])
        assert result.exit_code == 0
        mock_console.assert_called()


def test_completion_command_specific_shell(mock_console):
    """Test the completion command with specific shell."""
    result = runner.invoke(app, ["completion", "bash"])
    assert result.exit_code == 0
    mock_console.assert_called()


def test_completion_command_install(mock_console, tmp_path):
    """Test the completion command with installation."""
    rc_file = tmp_path / ".zshrc"
    rc_file.touch()

    with (
        patch("shellingham.detect_shell", return_value=("zsh", "/bin/zsh")),
        patch("os.path.expanduser", return_value=str(rc_file)),
        patch("typer.confirm", return_value=True),
    ):
        result = runner.invoke(app, ["completion", "--install"])
        assert result.exit_code == 0
        assert "repo --completion" in rc_file.read_text()


def test_repo_analyze_command(mock_settings, mock_console):
    """Test the repo analyze command."""
    result = runner.invoke(repo_app, ["analyze"])
    assert result.exit_code == 0
    mock_settings.assert_called_once()


def test_reports_list_command(mock_settings, mock_console):
    """Test the reports list command."""
    with patch("pathlib.Path.glob", return_value=[]):
        result = runner.invoke(reports_app, ["list"])
        assert result.exit_code == 1  # No reports found
        mock_settings.assert_called_once()


def test_logs_latest_command(mock_settings, mock_console):
    """Test the logs latest command."""
    with patch("pathlib.Path.exists", return_value=False):
        result = runner.invoke(logs_app, ["latest"])
        assert result.exit_code == 1  # No logs found
        mock_settings.assert_called_once()


def test_actions_list_command(mock_settings, mock_console):
    """Test the actions list command."""
    with patch("pathlib.Path.glob", return_value=[]):
        result = runner.invoke(actions_app, ["list"])
        assert result.exit_code == 1  # No actions found
        mock_settings.assert_called_once()


def test_command_group_help():
    """Test help text for each command group."""
    command_groups = [
        ("repo", repo_app),
        ("reports", reports_app),
        ("logs", logs_app),
        ("actions", actions_app),
    ]

    for name, group in command_groups:
        result = runner.invoke(group, ["--help"])
        assert result.exit_code == 0
        assert name in result.stdout.lower()


def test_command_group_integration():
    """Test that command groups are properly integrated."""
    command_groups = ["repo", "reports", "logs", "actions", "dev"]

    for group in command_groups:
        result = runner.invoke(app, [group, "--help"])
        assert result.exit_code == 0
        assert group in result.stdout.lower()


def test_invalid_command():
    """Test that invalid commands show help."""
    result = runner.invoke(app, ["invalid"])
    assert result.exit_code != 0
    assert "Usage:" in result.stdout
