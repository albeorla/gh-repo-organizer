"""Enhanced logging utility with rich formatting.

This module provides a Logger class that implements a Façade pattern over
the Rich console and standard file logging, simplifying the interface for
logging operations throughout the application.
"""

import datetime
import os
import time
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from repo_organizer.utils.rate_limiter import RateLimiter


class Logger:
    """Enhanced logging utility with rich formatting.

    This class serves as a Façade over Rich console logging and file-based logging,
    providing a unified interface for all logging operations.

    Attributes:
        log_file: Path to the log file
        console: Rich console for styled output
        debug_enabled: Whether to print debug-level logs to console
        stats: Dictionary of runtime statistics
        quiet_mode: Whether to minimize console output
        username: Username for tracking and attribution
    """

    def __init__(
        self,
        log_file: str,
        console: Console | None = None,
        debug_enabled: bool = False,
        quiet_mode: bool = False,
        username: str | None = None,
    ):
        """Initialize the logger.

        Args:
            log_file: Path to the log file
            console: Optional Rich console for output
            debug_enabled: Whether to print debug-level logs to console
            quiet_mode: Whether to minimize console output
            username: Optional username for tracking and attribution
        """
        self.log_file = log_file
        self.console = console or Console()
        self.debug_enabled = debug_enabled
        self.quiet_mode = quiet_mode
        self.username = username
        self.stats = {
            "start_time": time.time(),
            "repos_analyzed": 0,
            "repos_failed": 0,
            "repos_skipped": 0,
            "retries": 0,
        }

        # Use an instance-level lock to guarantee thread-safe writes to both
        # the log file and console. Multiple worker threads share the same Logger
        # instance when the application is executed with a ThreadPoolExecutor.
        from threading import Lock

        self._file_lock = Lock()
        self._console_lock = Lock()

    def set_username(self, username: str) -> None:
        """Set the username for logging and tracking.

        Args:
            username: Username to associate with log entries
        """
        self.username = username
        self.log(f"Username set to {username}", level="debug")

    def log(
        self,
        message: str,
        level: str = "info",
        username: str | None = None,
    ) -> None:
        """Log a message to both console and log file.

        Args:
            message: Message to log
            level: Log level (info, warning, error, success, debug)
            username: Optional username to associate with this specific log entry,
                      overrides the logger's default username
        """
        # Use the provided username or the default one
        effective_username = username or self.username

        # Only print to console if:
        # 1. Not in quiet mode, or level is error/warning
        # 2. Level is not debug or debug is enabled
        should_print_to_console = (not self.quiet_mode or level in ["error", "warning"]) and (
            level != "debug" or self.debug_enabled
        )

        # Special handling for API rate limit debug messages - don't print these
        # to console unless they're over a certain threshold to reduce clutter
        if level == "debug" and "Rate limit: Waiting" in message:
            wait_time = 0.0
            try:
                # Extract wait time from message
                wait_time = float(message.split("Waiting ")[1].split("s")[0])
            except (IndexError, ValueError):
                pass

            # Only print rate limit messages that exceed threshold
            if wait_time < 2.0:
                should_print_to_console = False

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Add color based on level
        log_message = message
        if "[" not in message[:5]:  # Don't add color if already styled
            if level == "warning":
                log_message = f"[yellow]{message}[/yellow]"
            elif level == "error":
                log_message = f"[red]{message}[/red]"
            elif level == "success":
                log_message = f"[green]{message}[/green]"
            elif level == "debug":
                log_message = f"[blue]DEBUG: {message}[/blue]"

        # Add username to console output if available
        user_prefix = f"[{effective_username}] " if effective_username else ""
        formatted_log_message = f"[{timestamp}] {user_prefix}{log_message}"

        # Get terminal width to truncate long messages if needed
        try:
            term_width = os.get_terminal_size().columns
            # Leave some room for potential progress bar characters
            max_log_width = max(40, term_width - 20)
            if len(message) > max_log_width:
                # Truncate very long messages to prevent line wrapping issues
                message_ellipsis = message[:max_log_width] + "..."
                if level == "warning":
                    log_message = f"[yellow]{message_ellipsis}[/yellow]"
                elif level == "error":
                    log_message = f"[red]{message_ellipsis}[/red]"
                elif level == "success":
                    log_message = f"[green]{message_ellipsis}[/green]"
                elif level == "debug":
                    log_message = f"[blue]DEBUG: {message_ellipsis}[/blue]"
                formatted_log_message = f"[{timestamp}] {user_prefix}{log_message}"
        except (OSError, AttributeError):
            # Terminal size might not be available in all environments
            pass

        # Ensure synchronization for console output to prevent interleaving with progress bars
        if should_print_to_console:
            with self._console_lock:
                # Add a newline before log message to separate from progress bar if present
                self.console.print(formatted_log_message)
                # Ensure a newline is printed after to avoid interference with progress bars
                if not formatted_log_message.endswith("\n"):
                    self.console.print("", end="\n")

        # Strip Rich markup for plain text log file and add username if available
        user_log_prefix = f"[{effective_username}] " if effective_username else ""
        plain_message = f"[{timestamp}] [{level.upper()}] {user_log_prefix}{message}"

        # Ensure only one thread writes to the log file at a time.
        with self._file_lock, open(self.log_file, "a") as logf:
            logf.write(plain_message + "\n")

    def update_stats(self, key: str, value: Any = 1, increment: bool = True) -> None:
        """Update statistics.

        Args:
            key: Statistic key to update
            value: Value to set or increment by
            increment: Whether to increment or set the value
        """
        if increment and key in self.stats:
            self.stats[key] += value
        else:
            self.stats[key] = value

    def print_summary(self, rate_limiters: list[RateLimiter] | None = None) -> None:
        """Print a summary of the run statistics.

        Args:
            rate_limiters: Optional list of rate limiters to include in stats
        """
        end_time = time.time()
        duration = end_time - self.stats["start_time"]

        summary = Table(title="Repository Analysis Summary", show_header=True)
        summary.add_column("Metric", style="cyan")
        summary.add_column("Value", style="green")

        summary.add_row("Total Duration", f"{duration:.2f} seconds")
        summary.add_row(
            "Repositories Analyzed",
            str(self.stats.get("repos_analyzed", 0)),
        )
        summary.add_row("Analysis Failures", str(self.stats.get("repos_failed", 0)))
        summary.add_row("Repositories Skipped", str(self.stats.get("repos_skipped", 0)))
        summary.add_row("API Retries", str(self.stats.get("retries", 0)))

        with self._console_lock:
            self.console.print(Panel(summary))

            # Rate limiting statistics
            if rate_limiters:
                rate_table = Table(
                    title="API Rate Limiting Statistics",
                    show_header=True,
                )
                rate_table.add_column("API", style="cyan")
                rate_table.add_column("Calls", justify="right")
                rate_table.add_column("Times Limited", justify="right")
                rate_table.add_column("Total Wait", justify="right")
                rate_table.add_column("% Limited", justify="right")

                for limiter in rate_limiters:
                    stats = limiter.get_stats()
                    rate_table.add_row(
                        stats["name"],
                        str(stats["total_calls"]),
                        str(stats["total_waits"]),
                        f"{stats['total_wait_time']:.2f}s",
                        f"{stats['pct_rate_limited']:.1f}%",
                    )

                self.console.print(Panel(rate_table))
