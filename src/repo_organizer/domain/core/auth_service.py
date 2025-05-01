"""Authentication service module for repository operations.

This module provides a centralized service for authentication validation and checking,
combining the validation logic with the configuration system.
"""

from repo_organizer.domain.core.auth_config import (
    AuthConfig,
    get_default_config,
    is_authentication_required,
)
from repo_organizer.domain.core.auth_validator import validate_username


class AuthService:
    """Authentication service for repository operations."""

    def __init__(self, auth_config: AuthConfig | None = None):
        """Initialize the authentication service.

        Args:
            auth_config: Optional custom authentication configuration
        """
        self.auth_config = auth_config or get_default_config()

    def validate_operation(
        self,
        operation_name: str,
        username: str | None = None,
    ) -> tuple[bool, str | None]:
        """Validate whether an operation can proceed based on authentication requirements.

        Args:
            operation_name: Name of the operation to validate
            username: Optional username for authentication

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if the operation can proceed, False otherwise
            - error_message: Error message explaining why validation failed, or None if valid
        """
        # Check if this operation requires authentication
        requires_auth = is_authentication_required(operation_name, self.auth_config)

        # If authentication is not required, allow the operation
        if not requires_auth:
            return True, None

        # Otherwise, validate the username
        validation_result = validate_username(username)
        if not validation_result.is_valid:
            return (
                False,
                f"Authentication required for '{operation_name}': {validation_result.error_message}",
            )

        # Username is valid and operation is authenticated
        return True, None

    def is_operation_allowed(
        self,
        operation_name: str,
        username: str | None = None,
    ) -> bool:
        """Check if an operation is allowed with the given authentication credentials.

        This is a simplified version of validate_operation that returns only a boolean.

        Args:
            operation_name: Name of the operation to check
            username: Optional username for authentication

        Returns:
            True if the operation is allowed, False otherwise
        """
        is_valid, _ = self.validate_operation(operation_name, username)
        return is_valid
