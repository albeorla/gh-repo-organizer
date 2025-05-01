"""Custom exceptions for the GitHub Repository Organizer.
"""


class APIError(Exception):
    """Custom exception for API-related errors that should be retried."""



class RateLimitExceededError(APIError):
    """Exception raised when API rate limits are exceeded."""



class AuthenticationError(APIError):
    """Exception raised when authentication with an API fails."""



class LLMServiceError(Exception):
    """Base exception for LLM service errors."""



class PromptEngineeringError(LLMServiceError):
    """Exception raised when there are issues with prompt engineering."""



class ResponseParsingError(LLMServiceError):
    """Exception raised when there are issues parsing LLM responses."""

