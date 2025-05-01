"""Tests for the authentication configuration module.
"""

from repo_organizer.domain.core.auth_config import (
    AuthConfig,
    AuthRequirement,
    OperationType,
    get_default_config,
    get_operations_requiring_auth,
    is_authentication_required,
)


class TestAuthConfig:
    """Tests for the authentication configuration module."""

    def test_get_default_config(self):
        """Test that default config is created with expected values."""
        config = get_default_config()

        # Verify default requirements
        assert (
            config.default_requirements[OperationType.READ_ONLY]
            == AuthRequirement.OPTIONAL
        )
        assert (
            config.default_requirements[OperationType.ANALYSIS]
            == AuthRequirement.REQUIRED
        )
        assert (
            config.default_requirements[OperationType.WRITE] == AuthRequirement.REQUIRED
        )
        assert (
            config.default_requirements[OperationType.ADMIN] == AuthRequirement.REQUIRED
        )

        # Verify operation categories exist
        assert "analyze" in config.operation_categories
        assert "cleanup" in config.operation_categories
        assert "list_repositories" in config.operation_categories

        # Verify categorization
        assert config.operation_categories["analyze"] == OperationType.ANALYSIS
        assert config.operation_categories["cleanup"] == OperationType.WRITE
        assert (
            config.operation_categories["list_repositories"] == OperationType.READ_ONLY
        )

    def test_is_authentication_required_default(self):
        """Test auth requirements using default configuration."""
        # Should require auth for analysis operations
        assert is_authentication_required("analyze") is True

        # Should require auth for write operations
        assert is_authentication_required("cleanup") is True

        # Should not require auth for read-only operations
        assert is_authentication_required("list_repositories") is False
        assert is_authentication_required("view_report") is False

        # Should require auth for admin operations
        assert is_authentication_required("execute_actions") is True

        # Uncategorized operations should require auth by default
        assert is_authentication_required("unknown_operation") is True

    def test_is_authentication_required_custom_config(self):
        """Test auth requirements with custom configuration."""
        # Create custom config
        config = AuthConfig()

        # Override defaults to make everything optional
        for op_type in OperationType:
            config.default_requirements[op_type] = AuthRequirement.OPTIONAL

        # Set specific overrides
        config.operation_overrides["list_repositories"] = AuthRequirement.REQUIRED
        config.operation_overrides["analyze"] = AuthRequirement.NOT_REQUIRED

        # Test with custom config
        assert is_authentication_required("list_repositories", config) is True
        assert is_authentication_required("analyze", config) is False
        assert is_authentication_required("cleanup", config) is False

        # Uncategorized operation with all defaults set to optional
        assert is_authentication_required("unknown_operation", config) is True

    def test_get_operations_requiring_auth(self):
        """Test getting the set of operations requiring authentication."""
        # With default config
        required_ops = get_operations_requiring_auth()

        # Verify analysis operations
        assert "analyze" in required_ops
        assert "generate_report" in required_ops

        # Verify write operations
        assert "cleanup" in required_ops
        assert "reset" in required_ops

        # Verify admin operations
        assert "execute_actions" in required_ops
        assert "delete_repository" in required_ops

        # Verify read-only operations are not included
        assert "list_repositories" not in required_ops
        assert "view_report" not in required_ops

        # Test with custom config
        config = AuthConfig()
        config.default_requirements[OperationType.READ_ONLY] = AuthRequirement.REQUIRED
        config.default_requirements[OperationType.ADMIN] = AuthRequirement.NOT_REQUIRED
        config.operation_overrides["analyze"] = AuthRequirement.NOT_REQUIRED

        custom_required_ops = get_operations_requiring_auth(config)

        # Read-only should now be required
        assert "list_repositories" in custom_required_ops
        assert "view_report" in custom_required_ops

        # Admin operations should no longer be required
        assert "execute_actions" not in custom_required_ops
        assert "delete_repository" not in custom_required_ops

        # Analyze has a specific override
        assert "analyze" not in custom_required_ops

        # But other analysis operations should be required
        assert "generate_report" in custom_required_ops
