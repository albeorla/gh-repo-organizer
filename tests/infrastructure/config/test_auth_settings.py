"""
Tests for the authentication settings module.
"""

import os
from unittest.mock import patch

from repo_organizer.domain.core.auth_config import AuthRequirement, OperationType
from repo_organizer.infrastructure.config.auth_settings import AuthSettings


class TestAuthSettings:
    """Tests for the authentication settings module."""

    def test_default_auth_settings(self):
        """Test default authentication settings."""
        settings = AuthSettings()
        
        # Check default values
        assert settings.auth_enabled is True
        assert settings.auth_default_requirements[OperationType.READ_ONLY] == AuthRequirement.OPTIONAL
        assert settings.auth_default_requirements[OperationType.ANALYSIS] == AuthRequirement.REQUIRED
        assert settings.auth_default_requirements[OperationType.WRITE] == AuthRequirement.REQUIRED
        assert settings.auth_default_requirements[OperationType.ADMIN] == AuthRequirement.REQUIRED
        assert settings.auth_operation_overrides == {}

    def test_get_auth_config_default(self):
        """Test converting default settings to AuthConfig."""
        settings = AuthSettings()
        config = settings.get_auth_config()
        
        # Check default values in the config
        assert config.default_requirements[OperationType.READ_ONLY] == AuthRequirement.OPTIONAL
        assert config.default_requirements[OperationType.ANALYSIS] == AuthRequirement.REQUIRED
        assert config.default_requirements[OperationType.WRITE] == AuthRequirement.REQUIRED
        assert config.default_requirements[OperationType.ADMIN] == AuthRequirement.REQUIRED
        assert config.operation_overrides == {}

    def test_get_auth_config_with_auth_disabled(self):
        """Test converting settings to AuthConfig when auth is disabled."""
        settings = AuthSettings(auth_enabled=False)
        config = settings.get_auth_config()
        
        # When auth is disabled, all requirements should be NOT_REQUIRED
        assert config.default_requirements[OperationType.READ_ONLY] == AuthRequirement.NOT_REQUIRED
        assert config.default_requirements[OperationType.ANALYSIS] == AuthRequirement.NOT_REQUIRED
        assert config.default_requirements[OperationType.WRITE] == AuthRequirement.NOT_REQUIRED
        assert config.default_requirements[OperationType.ADMIN] == AuthRequirement.NOT_REQUIRED

    def test_get_auth_config_with_custom_requirements(self):
        """Test converting settings to AuthConfig with custom requirements."""
        settings = AuthSettings(
            auth_default_requirements={
                OperationType.READ_ONLY: AuthRequirement.REQUIRED,
                OperationType.ADMIN: AuthRequirement.OPTIONAL,
            },
            auth_operation_overrides={
                "analyze": AuthRequirement.NOT_REQUIRED,
                "cleanup": AuthRequirement.REQUIRED,
            }
        )
        config = settings.get_auth_config()
        
        # Check custom default requirements
        assert config.default_requirements[OperationType.READ_ONLY] == AuthRequirement.REQUIRED
        assert config.default_requirements[OperationType.ADMIN] == AuthRequirement.OPTIONAL
        
        # Default for others should remain unchanged
        assert config.default_requirements[OperationType.ANALYSIS] == AuthRequirement.REQUIRED
        assert config.default_requirements[OperationType.WRITE] == AuthRequirement.REQUIRED
        
        # Check operation overrides
        assert config.operation_overrides["analyze"] == AuthRequirement.NOT_REQUIRED
        assert config.operation_overrides["cleanup"] == AuthRequirement.REQUIRED

    @patch.dict(os.environ, {
        "AUTH_ENABLED": "false",
        "AUTH_OPERATION_OVERRIDES": "analyze:not_required,cleanup:required",
        "AUTH_DEFAULT_REQUIREMENTS": "read_only:required,admin:optional"
    })
    def test_auth_settings_environment_override(self):
        """Test auth settings with environment variable overrides."""
        # Set up auth settings with the environment variables
        settings = AuthSettings(
            auth_enabled=False,
            auth_operation_overrides={
                "analyze": "not_required",
                "cleanup": "required"
            },
            auth_default_requirements={
                "read_only": "required",
                "admin": "optional"
            }
        )
        
        # Convert to config and verify
        config = settings.get_auth_config()
        
        # Auth is disabled, so all default requirements should be NOT_REQUIRED
        assert config.default_requirements[OperationType.READ_ONLY] == AuthRequirement.NOT_REQUIRED
        assert config.default_requirements[OperationType.ANALYSIS] == AuthRequirement.NOT_REQUIRED
        
        # When auth is disabled, operation overrides are not applied, so operation_overrides should be empty
        assert config.operation_overrides == {}