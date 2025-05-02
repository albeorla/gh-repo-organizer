"""Authentication logging implementation.

This module provides a specialized logger for authentication-related events,
ensuring proper security monitoring and audit trails.
"""

import datetime
import os
from pathlib import Path

from rich.console import Console

from repo_organizer.infrastructure.config.settings import Settings, load_settings
from repo_organizer.utils.logger import Logger


class AuthLogger:
    """Specialized logger for authentication events.

    This logger maintains separate log files for authentication events
    to support security monitoring and compliance requirements.

    Attributes:
        log_dir: Directory for authentication logs
        log_file: Path to the authentication log file
        console: Rich console for output
        logger: Base logger used for standard output
    """

    def __init__(
        self,
        console: Console | None = None,
        logger: Logger | None = None,
        settings: Settings | None = None,
    ):
        """Initialize the authentication logger.

        Args:
            console: Optional console for rich output
            logger: Optional base logger to relay messages to
            settings: Optional settings object for configuration
        """
        self.settings = settings or load_settings()
        self.console = console or Console()
        self.logger = logger

        # Create auth log directory
        self.log_dir = Path(self.settings.logs_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create a timestamped log file specifically for auth events
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"auth_log_{timestamp}.txt"

        # Create the log file if it doesn't exist
        if not self.log_file.exists():
            with open(self.log_file, "w") as f:
                f.write(f"# Authentication Log - Started {timestamp}\n")
                f.write(f"# Version: {self.settings.version}\n\n")

    def log_authentication_attempt(
        self,
        operation_name: str,
        username: str | None,
        success: bool,
        error_message: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Log an authentication attempt.

        Args:
            operation_name: Name of the operation being authenticated
            username: Username provided for authentication (can be None)
            success: Whether authentication succeeded
            error_message: Optional error message if authentication failed
            metadata: Optional additional metadata about the authentication attempt
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Format username or "anonymous" if None
        user_str = username if username else "anonymous"

        # Log status
        status = "SUCCESS" if success else "FAILURE"

        # Get IP information if available
        ip_address = os.environ.get(
            "REMOTE_ADDR",
            "localhost",
        )  # Will be localhost for CLI usage

        # Format the log entry
        log_entry = (
            f"[{timestamp}] [{status}] Operation: {operation_name} | "
            f"User: {user_str} | IP: {ip_address}"
        )

        # Add error message if present
        if error_message and not success:
            log_entry += f" | Error: {error_message}"

        # Add any additional metadata
        if metadata:
            metadata_str = " | ".join(f"{k}: {v}" for k, v in metadata.items())
            log_entry += f" | {metadata_str}"

        # Write to auth log file
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")

        # Also log to the standard logger if provided
        if self.logger:
            # Use appropriate log level
            level = "error" if not success else "debug"
            self.logger.log(
                f"Authentication {status}: {user_str} - {operation_name}",
                level=level,
            )
