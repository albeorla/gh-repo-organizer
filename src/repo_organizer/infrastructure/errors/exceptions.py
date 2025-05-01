"""Custom exceptions for the application.

This module provides custom exceptions for different error types
that can occur in the application, organized by layer.
"""

from typing import Any


# Base exceptions
class RepoOrganizerError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, *args: Any, **kwargs: Any):
        self.message = message
        super().__init__(message, *args)

        # Store additional context
        self.context = kwargs


# Domain layer exceptions
class DomainError(RepoOrganizerError):
    """Base exception for domain layer errors."""


class InvalidEntityError(DomainError):
    """Exception raised when an entity is invalid."""


class BusinessRuleViolationError(DomainError):
    """Exception raised when a business rule is violated."""


# Application layer exceptions
class ApplicationError(RepoOrganizerError):
    """Base exception for application layer errors."""


class UseCaseError(ApplicationError):
    """Exception raised when a use case fails."""


class ValidationError(ApplicationError):
    """Exception raised when validation fails."""


# Infrastructure layer exceptions
class InfrastructureError(RepoOrganizerError):
    """Base exception for infrastructure layer errors."""


class ConfigurationError(InfrastructureError):
    """Exception raised for configuration issues."""


class ExternalServiceError(InfrastructureError):
    """Base exception for external service errors."""


# GitHub-specific exceptions
class GitHubError(ExternalServiceError):
    """Base exception for GitHub API errors."""


class GitHubAuthenticationError(GitHubError):
    """Exception raised when authentication with GitHub fails."""


class GitHubRateLimitError(GitHubError):
    """Exception raised when GitHub API rate limit is exceeded."""


class GitHubResourceNotFoundError(GitHubError):
    """Exception raised when a GitHub resource is not found."""


# LLM-specific exceptions
class LLMError(ExternalServiceError):
    """Base exception for LLM API errors."""


class LLMAuthenticationError(LLMError):
    """Exception raised when authentication with LLM API fails."""


class LLMRateLimitError(LLMError):
    """Exception raised when LLM API rate limit is exceeded."""


class LLMResponseParsingError(LLMError):
    """Exception raised when parsing an LLM response fails."""


# Interface layer exceptions
class InterfaceError(RepoOrganizerError):
    """Base exception for interface layer errors."""


class CLIError(InterfaceError):
    """Exception raised for CLI errors."""


class AuthenticationError(InterfaceError):
    """Exception raised when user authentication fails."""


# File system exceptions
class FileSystemError(InfrastructureError):
    """Base exception for file system errors."""


class FileNotFoundError(FileSystemError):
    """Exception raised when a file is not found."""


class DirectoryNotFoundError(FileSystemError):
    """Exception raised when a directory is not found."""


class WritePermissionError(FileSystemError):
    """Exception raised when write permission is denied."""
