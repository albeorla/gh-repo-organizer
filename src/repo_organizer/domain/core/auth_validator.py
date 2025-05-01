"""Authentication validation module for repository operations.

This module provides functions to validate user authentication
before executing operations.
"""

import re
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of a username validation operation."""

    is_valid: bool
    error_message: str | None = None


def validate_username(username: str | None) -> ValidationResult:
    """Validate that a username is properly formatted and not empty.

    Args:
        username: The username to validate

    Returns:
        ValidationResult with validation status and error message if invalid
    """
    # Check if username is None or empty
    if username is None:
        return ValidationResult(is_valid=False, error_message="Username is required")

    # Check if username is empty string or only whitespace
    if not username or username.strip() == "":
        return ValidationResult(
            is_valid=False,
            error_message="Username cannot be empty",
        )

    # Check minimum and maximum length
    if len(username) < 3:
        return ValidationResult(
            is_valid=False,
            error_message="Username must be at least 3 characters",
        )

    if len(username) > 50:
        return ValidationResult(
            is_valid=False,
            error_message="Username cannot exceed 50 characters",
        )

    # Check username format (alphanumeric with optional hyphens, underscores)
    # GitHub usernames allow alphanumeric characters and hyphens
    pattern = r"^[a-zA-Z0-9][-a-zA-Z0-9_]*$"
    if not re.match(pattern, username):
        return ValidationResult(
            is_valid=False,
            error_message="Username must start with a letter or number and can only contain letters, numbers, hyphens (-), and underscores (_)",
        )

    # Username is valid
    return ValidationResult(is_valid=True)
