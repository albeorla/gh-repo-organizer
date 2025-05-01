"""Tests for the authentication validator module."""

from repo_organizer.domain.core.auth_validator import validate_username


class TestAuthValidator:
    """Tests for the authentication validator functions."""

    def test_validate_username_valid(self):
        """Test validation with valid usernames."""
        valid_usernames = [
            "user123",
            "john-doe",
            "jane_doe",
            "developer42",
            "a-long-username-but-still-valid",
            "123abc",  # Valid: GitHub allows usernames starting with numbers
        ]

        for username in valid_usernames:
            result = validate_username(username)
            assert result.is_valid, (
                f"Username '{username}' should be valid, got error: {result.error_message}"
            )
            assert result.error_message is None

    def test_validate_username_none(self):
        """Test validation with None username."""
        result = validate_username(None)
        assert not result.is_valid
        assert "required" in result.error_message.lower()

    def test_validate_username_empty(self):
        """Test validation with empty username."""
        result = validate_username("")
        assert not result.is_valid
        assert "empty" in result.error_message.lower()

        # Test whitespace-only username
        result = validate_username("   ")
        assert not result.is_valid
        assert "empty" in result.error_message.lower()

    def test_validate_username_too_short(self):
        """Test validation with too short username."""
        result = validate_username("ab")
        assert not result.is_valid
        assert "at least 3 characters" in result.error_message.lower()

    def test_validate_username_too_long(self):
        """Test validation with too long username."""
        result = validate_username("a" * 51)
        assert not result.is_valid
        assert "exceed 50 characters" in result.error_message.lower()

    def test_validate_username_invalid_format(self):
        """Test validation with invalid username format."""
        invalid_usernames = [
            "user name",  # Contains space
            "user@name",  # Contains @
            "-username",  # Starts with hyphen
            "_username",  # Starts with underscore
            "user$name",  # Contains special character
            "user/name",  # Contains slash
            "user\\name",  # Contains backslash
        ]

        for username in invalid_usernames:
            result = validate_username(username)
            assert not result.is_valid, f"Username '{username}' should be invalid"
            assert result.error_message is not None
