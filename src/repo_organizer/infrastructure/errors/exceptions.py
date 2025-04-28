"""
Custom exceptions for the application.

This module provides custom exceptions for different error types
that can occur in the application, organized by layer.
"""

from typing import Optional, Any, Dict, List


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
    pass


class InvalidEntityError(DomainError):
    """Exception raised when an entity is invalid."""
    pass


class BusinessRuleViolationError(DomainError):
    """Exception raised when a business rule is violated."""
    pass


# Application layer exceptions
class ApplicationError(RepoOrganizerError):
    """Base exception for application layer errors."""
    pass


class UseCaseError(ApplicationError):
    """Exception raised when a use case fails."""
    pass


class ValidationError(ApplicationError):
    """Exception raised when validation fails."""
    pass


# Infrastructure layer exceptions
class InfrastructureError(RepoOrganizerError):
    """Base exception for infrastructure layer errors."""
    pass


class ConfigurationError(InfrastructureError):
    """Exception raised for configuration issues."""
    pass


class ExternalServiceError(InfrastructureError):
    """Base exception for external service errors."""
    pass


# GitHub-specific exceptions
class GitHubError(ExternalServiceError):
    """Base exception for GitHub API errors."""
    pass


class GitHubAuthenticationError(GitHubError):
    """Exception raised when authentication with GitHub fails."""
    pass


class GitHubRateLimitError(GitHubError):
    """Exception raised when GitHub API rate limit is exceeded."""
    pass


class GitHubResourceNotFoundError(GitHubError):
    """Exception raised when a GitHub resource is not found."""
    pass


# LLM-specific exceptions
class LLMError(ExternalServiceError):
    """Base exception for LLM API errors."""
    pass


class LLMAuthenticationError(LLMError):
    """Exception raised when authentication with LLM API fails."""
    pass


class LLMRateLimitError(LLMError):
    """Exception raised when LLM API rate limit is exceeded."""
    pass


class LLMResponseParsingError(LLMError):
    """Exception raised when parsing an LLM response fails."""
    pass


# Interface layer exceptions
class InterfaceError(RepoOrganizerError):
    """Base exception for interface layer errors."""
    pass


class CLIError(InterfaceError):
    """Exception raised for CLI errors."""
    pass


# File system exceptions
class FileSystemError(InfrastructureError):
    """Base exception for file system errors."""
    pass


class FileNotFoundError(FileSystemError):
    """Exception raised when a file is not found."""
    pass


class DirectoryNotFoundError(FileSystemError):
    """Exception raised when a directory is not found."""
    pass


class WritePermissionError(FileSystemError):
    """Exception raised when write permission is denied."""
    pass