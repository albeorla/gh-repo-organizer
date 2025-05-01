"""Authentication configuration module for repository operations.

This module defines the authentication requirements for different operation types
and provides functions to check if specific operations require authentication.
"""

from enum import Enum

from pydantic import BaseModel, Field


class OperationType(str, Enum):
    """Types of operations that can be performed."""

    READ_ONLY = "read_only"  # Operations that only read data
    ANALYSIS = "analysis"  # Operations that analyze repositories
    WRITE = "write"  # Operations that write/modify data
    ADMIN = "admin"  # Administrative operations


class AuthRequirement(str, Enum):
    """Authentication requirement level for operations."""

    REQUIRED = "required"  # Authentication is always required
    OPTIONAL = "optional"  # Authentication is optional
    NOT_REQUIRED = "not_required"  # Authentication is not required


class AuthConfig(BaseModel):
    """Authentication configuration for the application."""

    # Default requirements by operation type
    default_requirements: dict[OperationType, AuthRequirement] = Field(
        default_factory=lambda: {
            OperationType.READ_ONLY: AuthRequirement.OPTIONAL,
            OperationType.ANALYSIS: AuthRequirement.REQUIRED,
            OperationType.WRITE: AuthRequirement.REQUIRED,
            OperationType.ADMIN: AuthRequirement.REQUIRED,
        },
        description="Default authentication requirements by operation type",
    )

    # Override requirements for specific operations
    operation_overrides: dict[str, AuthRequirement] = Field(
        default_factory=dict,
        description="Override authentication requirements for specific operations",
    )

    # Operations categorized by type
    operation_categories: dict[str, OperationType] = Field(
        default_factory=lambda: {
            # Read-only operations
            "list_repositories": OperationType.READ_ONLY,
            "view_report": OperationType.READ_ONLY,
            "view_logs": OperationType.READ_ONLY,
            # Analysis operations
            "analyze": OperationType.ANALYSIS,
            "generate_report": OperationType.ANALYSIS,
            # Write operations
            "cleanup": OperationType.WRITE,
            "reset": OperationType.WRITE,
            # Admin operations
            "delete_repository": OperationType.ADMIN,
            "archive_repository": OperationType.ADMIN,
            "execute_actions": OperationType.ADMIN,
        },
        description="Categorization of operations by type",
    )

    class Config:
        """Model configuration."""

        use_enum_values = True


def get_default_config() -> AuthConfig:
    """Get the default authentication configuration.

    Returns:
        Default AuthConfig with predefined settings
    """
    return AuthConfig()


def is_authentication_required(
    operation_name: str,
    config: AuthConfig | None = None,
) -> bool:
    """Check if authentication is required for the given operation.

    Args:
        operation_name: Name of the operation to check
        config: Optional custom auth configuration

    Returns:
        True if authentication is required, False otherwise
    """
    if not config:
        config = get_default_config()

    # First check if there's a specific override for this operation
    if operation_name in config.operation_overrides:
        return config.operation_overrides[operation_name] == AuthRequirement.REQUIRED

    # Then check the operation category
    if operation_name in config.operation_categories:
        operation_type = config.operation_categories[operation_name]
        return config.default_requirements[operation_type] == AuthRequirement.REQUIRED

    # If the operation is not categorized, default to requiring authentication for safety
    return True


def get_operations_requiring_auth(config: AuthConfig | None = None) -> set[str]:
    """Get the set of all operations that require authentication.

    Args:
        config: Optional custom auth configuration

    Returns:
        Set of operation names that require authentication
    """
    if not config:
        config = get_default_config()

    result = set()

    # Add operations with explicit overrides requiring authentication
    for op_name, req in config.operation_overrides.items():
        if req == AuthRequirement.REQUIRED:
            result.add(op_name)

    # Add operations that require authentication based on their category
    for op_name, op_type in config.operation_categories.items():
        # Skip if there's a specific override
        if op_name in config.operation_overrides:
            continue

        # Add if the operation type requires authentication
        if config.default_requirements[op_type] == AuthRequirement.REQUIRED:
            result.add(op_name)

    return result
