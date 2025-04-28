"""
Settings management module implementing Repository pattern for configuration.

This module provides a centralized configuration management system using
the Repository pattern, allowing access to configuration values from
multiple sources (environment variables, config files, etc).
"""

import os
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


class Settings(BaseSettings):
    """Application settings using Pydantic for validation.

    This class follows the Repository pattern for configuration management,
    providing a clean interface to access configuration values.
    """

    # API keys
    anthropic_api_key: str = Field(..., description="Anthropic API key")
    github_token: str = Field(..., description="GitHub Personal Access Token")

    # GitHub configuration
    github_username: Optional[str] = Field(None, description="GitHub username for API requests")

    # Repository organizer settings
    output_dir: str = Field(".out/repos", description="Directory for output files")
    logs_dir: str = Field(".logs", description="Directory for log files")
    max_repos: int = Field(100, description="Maximum number of repositories to process")

    # LLM settings
    llm_model: str = Field("claude-3-7-sonnet-latest", description="LLM model to use")
    llm_temperature: float = Field(0.2, description="LLM temperature (0.0-1.0)")
    llm_thinking_enabled: bool = Field(
        True, description="Enable extended thinking for LLM"
    )
    llm_thinking_budget: int = Field(16000, description="Token budget for LLM thinking")

    # Concurrency and rate limiting
    max_workers: int = Field(5, description="Number of parallel workers")
    github_rate_limit: int = Field(30, description="GitHub API calls per minute")
    llm_rate_limit: int = Field(10, description="LLM API calls per minute")

    # Debug settings
    debug_logging: bool = Field(False, description="Enable debug logging")
    quiet_mode: bool = Field(False, description="Minimize console output")

    # Application settings
    log_level: str = Field("INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    cache_dir: str = Field("~/.repo_organizer/cache", description="Directory for caching data")

    # Feature flags
    enable_analytics: bool = Field(False, description="Enable usage analytics")
    debug_mode: bool = Field(False, description="Enable debug mode with additional logging")

    @field_validator('github_token')
    def validate_github_token(cls, v):
        if not v or len(v) < 10:
            raise ValueError("GitHub token is required and must be valid")
        return v

    @field_validator("output_dir", "logs_dir")
    def create_directory(cls, v: str) -> str:  # noqa: D401
        """Return a fully-qualified path and guarantee the directory exists.

        The path supplied by the user may contain *nix style home
        shortcuts (``~``) or environment variables (e.g. ``$HOME``) which
        need to be resolved before the directory can be created.  We
        therefore expand them first and then convert the result to an
        absolute path so the rest of the application can rely on a
        canonical representation.
        """

        # Expand ``~`` to the user home and any *nix environment
        # variables that may be present in the supplied string.
        expanded = os.path.expanduser(os.path.expandvars(v))

        # Convert to an absolute path so there is only ever a single,
        # fully-qualified representation of the directory in the rest of
        # the codebase.
        abs_path = os.path.abspath(expanded)

        # Finally, ensure the directory exists.  ``exist_ok=True`` makes
        # the call idempotent so the validator can run multiple times
        # safely during the lifetime of the application.
        os.makedirs(abs_path, exist_ok=True)

        return abs_path

    model_config = {
        "env_prefix": "REPO_ORGANIZER_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }


def load_settings(env_file: Optional[str] = None) -> Settings:
    """Load settings from environment or .env file.

    This function implements the Factory pattern to create a validated
    Settings object.

    Args:
        env_file: Optional path to .env file

    Returns:
        Validated Settings object
    """
    # Load environment variables from .env file if specified
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    # Extract settings from environment
    # Allow users to override the default paths via environment variables as
    # documented in the README.  Fallback to the previous defaults if the
    # variables are not provided so existing behaviour is preserved.
    settings_dict = {
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "github_token": os.getenv("GITHUB_TOKEN", ""),
        "github_username": os.getenv("GITHUB_USERNAME"),
        "output_dir": os.getenv("OUTPUT_DIR", ".out/repos"),
        "logs_dir": os.getenv("LOGS_DIR", ".logs"),
        "max_repos": int(os.getenv("MAX_REPOS", "100")),
        "max_workers": int(os.getenv("MAX_WORKERS", "5")),
        "github_rate_limit": int(os.getenv("GITHUB_RATE_LIMIT", "30")),
        "llm_rate_limit": int(os.getenv("LLM_RATE_LIMIT", "10")),
        "debug_logging": os.getenv("DEBUG_LOGGING", "false").lower() == "true",
        "quiet_mode": os.getenv("QUIET_MODE", "false").lower() == "true",
        # LLM settings
        "llm_model": os.getenv("LLM_MODEL", "claude-3-7-sonnet-latest"),
        "llm_temperature": float(os.getenv("LLM_TEMPERATURE", "0.2")),
        "llm_thinking_enabled": os.getenv("LLM_THINKING_ENABLED", "true").lower()
        == "true",
        "llm_thinking_budget": int(os.getenv("LLM_THINKING_BUDGET", "16000")),
        # Application settings
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "cache_dir": os.getenv("CACHE_DIR", "~/.repo_organizer/cache"),
        # Feature flags
        "enable_analytics": os.getenv("ENABLE_ANALYTICS", "false").lower() == "true",
        "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true",
    }

    # Create and validate settings
    return Settings(**settings_dict)
