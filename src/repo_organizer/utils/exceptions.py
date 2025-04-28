"""
Custom exceptions for the GitHub Repository Organizer.
"""


class APIError(Exception):
    """Custom exception for API-related errors that should be retried."""

    pass


class RateLimitExceededError(APIError):
    """Exception raised when API rate limits are exceeded."""

    pass


class AuthenticationError(APIError):
    """Exception raised when authentication with an API fails."""

    pass


class LLMServiceError(Exception):
    """Base exception for LLM service errors."""

    pass


class PromptEngineeringError(LLMServiceError):
    """Exception raised when there are issues with prompt engineering."""

    pass


class ResponseParsingError(LLMServiceError):
    """Exception raised when there are issues parsing LLM responses."""

    pass
