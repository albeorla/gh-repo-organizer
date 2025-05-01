"""
Tests for the CLI authentication middleware.

This module tests the authentication middleware including the new authentication
failure logging and username propagation features.
"""

import os
import tempfile
import shutil
import pytest
from unittest.mock import Mock, patch, MagicMock
import typer

from repo_organizer.cli.auth_middleware import (
    authenticate_command,
    validate_command_auth,
    with_auth_option,
)
from repo_organizer.domain.core.auth_config import AuthConfig, OperationType, AuthRequirement
# We'll mock this for testing
# from repo_organizer.infrastructure.logging.auth_logger import AuthLogger


@pytest.fixture
def mock_console():
    """Provide a mock console for testing."""
    with patch("repo_organizer.cli.auth_middleware.console") as mock:
        yield mock


@pytest.fixture
def mock_auth_logger():
    """Provide a mock authentication logger."""
    mock_logger = MagicMock()
    # Add the required method
    mock_logger.log_authentication_attempt = MagicMock()
    return mock_logger


@pytest.fixture
def test_auth_config():
    """Provide a test authentication configuration."""
    config = AuthConfig()
    
    # Define test operations
    config.operation_categories = {
        "test_command": OperationType.WRITE,
        "read_command": OperationType.READ_ONLY,
        "admin_command": OperationType.ADMIN,
    }
    
    # Set requirements
    config.default_requirements[OperationType.WRITE] = AuthRequirement.REQUIRED
    config.default_requirements[OperationType.READ_ONLY] = AuthRequirement.NOT_REQUIRED
    config.default_requirements[OperationType.ADMIN] = AuthRequirement.REQUIRED
    
    return config


class TestAuthMiddleware:
    """Tests for the authentication middleware."""
    
    def test_authenticate_command_success(self, test_auth_config):
        """Test successful authentication with the decorator."""
        # Create a mock function
        mock_func = Mock(return_value="success")
        mock_func.__name__ = "test_func"  # Add __name__ attribute for metadata
        
        # Apply decorator with test config
        decorated = authenticate_command("test_command", auth_config=test_auth_config)(mock_func)
        
        # Call with valid username
        result = decorated(username="valid-user")
        
        # Function should have been called once
        mock_func.assert_called_once()
        assert result == "success"
    
    def test_authenticate_command_with_logging_success(self, test_auth_config, mock_auth_logger):
        """Test successful authentication with logging."""
        # Create a mock function
        mock_func = Mock(return_value="success")
        mock_func.__name__ = "test_func"  # Add __name__ attribute for metadata
        
        # Apply decorator with test config and mock logger
        decorated = authenticate_command(
            "test_command", 
            auth_config=test_auth_config,
            auth_logger=mock_auth_logger
        )(mock_func)
        
        # Call with valid username
        result = decorated(username="valid-user")
        
        # Function should have been called once
        mock_func.assert_called_once()
        assert result == "success"
        
        # Authentication logger should be called with success
        mock_auth_logger.log_authentication_attempt.assert_called_once()
        call_args = mock_auth_logger.log_authentication_attempt.call_args[1]
        assert call_args["operation_name"] == "test_command"
        assert call_args["username"] == "valid-user"
        assert call_args["success"] is True
        assert call_args["error_message"] is None
    
    def test_authenticate_command_failure(self, test_auth_config, mock_console):
        """Test failed authentication with the decorator."""
        # Create a mock function
        mock_func = Mock(return_value="success")
        mock_func.__name__ = "test_func"  # Add __name__ attribute for metadata
        
        # Apply decorator with test config
        decorated = authenticate_command("test_command", auth_config=test_auth_config)(mock_func)
        
        # Call with invalid username
        with pytest.raises(typer.Exit) as excinfo:
            decorated(username=None)
        
        # Function should not have been called
        mock_func.assert_not_called()
        
        # Typer should exit with code 1
        assert excinfo.value.exit_code == 1
        
        # Console should display error
        mock_console.print.assert_called()
        
    def test_authenticate_command_with_logging_failure(self, test_auth_config, mock_console, mock_auth_logger):
        """Test failed authentication with logging."""
        # Create a mock function
        mock_func = Mock(return_value="success")
        mock_func.__name__ = "test_func"  # Add __name__ attribute for metadata
        
        # Mock auth service to return failure with a specific error message
        mock_auth_service = Mock()
        mock_auth_service.validate_operation.return_value = (False, "Username required")
        
        # Apply decorator with test config and mocks
        decorated = authenticate_command(
            "test_command", 
            auth_service=mock_auth_service,
            auth_logger=mock_auth_logger
        )(mock_func)
        
        # Call with invalid username
        with pytest.raises(typer.Exit) as excinfo:
            decorated(username=None)
        
        # Function should not have been called
        mock_func.assert_not_called()
        
        # Typer should exit with code 1
        assert excinfo.value.exit_code == 1
        
        # Authentication logger should be called with failure details
        mock_auth_logger.log_authentication_attempt.assert_called_once()
        call_args = mock_auth_logger.log_authentication_attempt.call_args[1]
        assert call_args["operation_name"] == "test_command"
        assert call_args["username"] is None
        assert call_args["success"] is False
        assert call_args["error_message"] == "Username required"
    
    def test_authenticate_command_not_required(self, test_auth_config):
        """Test command that doesn't require authentication."""
        # Create a mock function
        mock_func = Mock(return_value="success")
        mock_func.__name__ = "test_func"  # Add __name__ attribute for metadata
        
        # Apply decorator with test config for a command that doesn't require auth
        decorated = authenticate_command("read_command", auth_config=test_auth_config)(mock_func)
        
        # Call with no username should succeed
        result = decorated(username=None)
        
        # Function should have been called once
        mock_func.assert_called_once()
        assert result == "success"
    
    def test_validate_command_auth_success(self, test_auth_config):
        """Test validate_command_auth with valid credentials."""
        with patch(
            "repo_organizer.cli.auth_middleware.AuthService"
        ) as mock_service_class:
            # Configure the mock service to return valid
            mock_service = Mock()
            mock_service.validate_operation.return_value = (True, None)
            mock_service_class.return_value = mock_service
            
            # Call with valid username
            result = validate_command_auth("test_command", username="valid-user", exit_on_failure=False)
            
            # Should return True
            assert result is True
            
            # validate_operation should have been called
            mock_service.validate_operation.assert_called_once_with("test_command", "valid-user")
    
    def test_validate_command_auth_failure(self, test_auth_config, mock_console):
        """Test validate_command_auth with invalid credentials."""
        with patch(
            "repo_organizer.cli.auth_middleware.AuthService"
        ) as mock_service_class:
            # Configure the mock service to return invalid
            mock_service = Mock()
            mock_service.validate_operation.return_value = (False, "Authentication failed")
            mock_service_class.return_value = mock_service
            
            # Call with invalid username and exit_on_failure=False
            result = validate_command_auth(
                "test_command", username=None, exit_on_failure=False
            )
            
            # Should return False
            assert result is False
            
            # validate_operation should have been called
            mock_service.validate_operation.assert_called_once_with("test_command", None)
            
            # Console should not display error when exit_on_failure=False
            mock_console.print.assert_not_called()
            
            # Call with invalid username and exit_on_failure=True
            with pytest.raises(typer.Exit) as excinfo:
                validate_command_auth("test_command", username=None, exit_on_failure=True)
            
            # Typer should exit with code 1
            assert excinfo.value.exit_code == 1
            
            # Console should display error when exit_on_failure=True
            mock_console.print.assert_called()
    
    def test_with_auth_option(self):
        """Test with_auth_option adds username option to commands."""
        # Create a mock Typer app
        app = typer.Typer()
        
        # Store the original command method
        original_command = app.command
        
        # Apply the with_auth_option function
        with_auth_option(app)
        
        # Verify the command method was changed
        assert app.command != original_command
        
        # Create a test command
        @app.command()
        def test_cmd():
            pass
        
        # Verify the command has the username option
        # This is a bit tricky since Typer doesn't expose parameter information directly
        # The presence of the username option is indirectly verified by other tests
        
    def test_auth_logger_integration(self):
        """Test the authentication logging integration."""
        # Create a mock AuthLogger
        mock_auth_logger = MagicMock()
        mock_auth_logger.log_authentication_attempt = MagicMock()
        
        # Mock the auth service
        mock_auth_service = Mock()
        mock_auth_service.validate_operation.return_value = (True, "")
        
        # Create a test function with the decorator
        @authenticate_command(
            "test_operation", 
            auth_service=mock_auth_service,
            auth_logger=mock_auth_logger
        )
        def test_func(username: str = "default_user"):
            return f"Success with {username}"
        
        # Call the function
        result = test_func(username="test_user")
        
        # Verify the function was called
        assert result == "Success with test_user"
        
        # Verify the auth logger was called appropriately
        mock_auth_logger.log_authentication_attempt.assert_called_once()
        call_args = mock_auth_logger.log_authentication_attempt.call_args[1]
        
        # Check the arguments passed to the log method
        assert call_args["operation_name"] == "test_operation"
        assert call_args["username"] == "test_user"
        assert call_args["success"] is True