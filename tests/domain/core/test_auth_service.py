"""Tests for the authentication service module."""

from repo_organizer.domain.core.auth_config import (
    AuthConfig,
    AuthRequirement,
    OperationType,
)
from repo_organizer.domain.core.auth_service import AuthService


class TestAuthService:
    """Tests for the authentication service."""

    def test_validate_operation_not_requiring_auth(self):
        """Test validation of operations that don't require authentication."""
        # Create a custom config for testing
        config = AuthConfig()
        config.operation_categories["test_operation"] = OperationType.READ_ONLY
        config.default_requirements[OperationType.READ_ONLY] = AuthRequirement.NOT_REQUIRED

        # Create auth service with custom config
        auth_service = AuthService(auth_config=config)

        # Operation should succeed even without a username
        is_valid, error_message = auth_service.validate_operation("test_operation")
        assert is_valid is True
        assert error_message is None

        # Operation should succeed with invalid username (since auth is not required)
        is_valid, error_message = auth_service.validate_operation("test_operation", "")
        assert is_valid is True
        assert error_message is None

    def test_validate_operation_requiring_auth(self):
        """Test validation of operations that require authentication."""
        # Create a custom config for testing
        config = AuthConfig()
        config.operation_categories["test_operation"] = OperationType.WRITE
        config.default_requirements[OperationType.WRITE] = AuthRequirement.REQUIRED

        # Create auth service with custom config
        auth_service = AuthService(auth_config=config)

        # Operation should fail without a username
        is_valid, error_message = auth_service.validate_operation("test_operation")
        assert is_valid is False
        assert "Authentication required" in error_message

        # Operation should fail with invalid username
        is_valid, error_message = auth_service.validate_operation("test_operation", "")
        assert is_valid is False
        assert "Authentication required" in error_message

        # Operation should succeed with valid username
        is_valid, error_message = auth_service.validate_operation(
            "test_operation",
            "valid-user",
        )
        assert is_valid is True
        assert error_message is None

    def test_validate_operation_with_invalid_usernames(self):
        """Test validation with various invalid usernames."""
        # Create a config that requires auth for all operations
        config = AuthConfig()
        for op_type in OperationType:
            config.default_requirements[op_type] = AuthRequirement.REQUIRED

        # Create auth service with custom config
        auth_service = AuthService(auth_config=config)

        # Test with None username
        is_valid, error_message = auth_service.validate_operation("any_operation", None)
        assert is_valid is False
        assert "required" in error_message.lower()

        # Test with empty string
        is_valid, error_message = auth_service.validate_operation("any_operation", "")
        assert is_valid is False
        assert "empty" in error_message.lower()

        # Test with too short username
        is_valid, error_message = auth_service.validate_operation("any_operation", "ab")
        assert is_valid is False
        assert "at least 3 characters" in error_message.lower()

        # Test with invalid format
        is_valid, error_message = auth_service.validate_operation(
            "any_operation",
            "user@domain",
        )
        assert is_valid is False
        assert "must start with" in error_message.lower()

    def test_is_operation_allowed(self):
        """Test the simplified is_operation_allowed method."""
        # Create a custom config for testing
        config = AuthConfig()
        config.operation_categories["allowed_op"] = OperationType.READ_ONLY
        config.default_requirements[OperationType.READ_ONLY] = AuthRequirement.NOT_REQUIRED

        config.operation_categories["auth_op"] = OperationType.WRITE
        config.default_requirements[OperationType.WRITE] = AuthRequirement.REQUIRED

        # Create auth service with custom config
        auth_service = AuthService(auth_config=config)

        # Test operation that doesn't require auth
        assert auth_service.is_operation_allowed("allowed_op") is True
        assert auth_service.is_operation_allowed("allowed_op", None) is True
        assert auth_service.is_operation_allowed("allowed_op", "") is True

        # Test operation that requires auth
        assert auth_service.is_operation_allowed("auth_op") is False
        assert auth_service.is_operation_allowed("auth_op", None) is False
        assert auth_service.is_operation_allowed("auth_op", "") is False
        assert auth_service.is_operation_allowed("auth_op", "valid-user") is True
