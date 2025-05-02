"""Authentication settings module for the repository organizer.

This module extends the core settings to include authentication configuration options.
"""

import os

from pydantic import Field

from repo_organizer.domain.core.auth_config import (
    AuthConfig,
    AuthRequirement,
    OperationType,
)
from repo_organizer.infrastructure.config.settings import Settings, load_settings


class AuthSettings(Settings):
    """Extended settings class with authentication configuration."""

    # Authentication settings
    auth_enabled: bool = Field(
        True,
        description="Whether authentication is globally enabled",
    )

    auth_default_requirements: dict[str, str] = Field(
        default_factory=lambda: {
            OperationType.READ_ONLY: AuthRequirement.OPTIONAL,
            OperationType.ANALYSIS: AuthRequirement.REQUIRED,
            OperationType.WRITE: AuthRequirement.REQUIRED,
            OperationType.ADMIN: AuthRequirement.REQUIRED,
        },
        description="Default authentication requirements by operation type",
    )

    auth_operation_overrides: dict[str, str] = Field(
        default_factory=dict,
        description="Override authentication requirements for specific operations",
    )

    def get_auth_config(self) -> AuthConfig:
        """Convert settings to an AuthConfig object.

        Returns:
            AuthConfig based on current settings
        """
        # Create a default config
        config = AuthConfig()

        # Apply settings-based customizations
        if not self.auth_enabled:
            # If auth is globally disabled, set all default requirements to NOT_REQUIRED
            for op_type in OperationType:
                config.default_requirements[op_type] = AuthRequirement.NOT_REQUIRED
        else:
            # Apply custom default requirements
            for op_type_str, requirement_str in self.auth_default_requirements.items():
                try:
                    op_type = OperationType(op_type_str)
                    requirement = AuthRequirement(requirement_str)
                    config.default_requirements[op_type] = requirement
                except (ValueError, KeyError):
                    # Skip invalid values
                    pass

            # Apply operation-specific overrides
            for op_name, requirement_str in self.auth_operation_overrides.items():
                try:
                    requirement = AuthRequirement(requirement_str)
                    config.operation_overrides[op_name] = requirement
                except ValueError:
                    # Skip invalid values
                    pass

        return config


def load_auth_settings(env_file: str | None = None) -> AuthSettings:
    """Load authentication settings from environment or .env file.

    Args:
        env_file: Optional path to .env file

    Returns:
        AuthSettings object
    """
    # Start with the standard settings
    settings = load_settings(env_file)
    settings_dict = settings.model_dump()

    # Add authentication settings
    settings_dict.update(
        {
            "auth_enabled": os.getenv("AUTH_ENABLED", "true").lower() == "true",
        },
    )

    # Parse operation overrides if provided
    auth_overrides_str = os.getenv("AUTH_OPERATION_OVERRIDES", "")
    if auth_overrides_str:
        try:
            # Format expected: "operation1:required,operation2:optional,..."
            overrides = {}
            for item in auth_overrides_str.split(","):
                if ":" in item:
                    op_name, requirement = item.split(":", 1)
                    overrides[op_name.strip()] = requirement.strip()
            settings_dict["auth_operation_overrides"] = overrides
        except Exception:
            # If parsing fails, use empty dict
            settings_dict["auth_operation_overrides"] = {}

    # Parse default requirements if provided
    auth_defaults_str = os.getenv("AUTH_DEFAULT_REQUIREMENTS", "")
    if auth_defaults_str:
        try:
            # Format expected: "read_only:optional,analysis:required,..."
            defaults = {}
            for item in auth_defaults_str.split(","):
                if ":" in item:
                    op_type, requirement = item.split(":", 1)
                    defaults[op_type.strip()] = requirement.strip()
            settings_dict["auth_default_requirements"] = defaults
        except Exception:
            # If parsing fails, use default requirements
            pass

    return AuthSettings(**settings_dict)
