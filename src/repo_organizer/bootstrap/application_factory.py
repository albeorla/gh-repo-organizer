"""
Application factory module for creating application instances.

This module implements the Factory Method pattern to create the application
and its components with proper dependency injection.
"""

from typing import Optional, Callable

from rich.console import Console

from repo_organizer.bootstrap.application_runner import ApplicationRunner
from repo_organizer.infrastructure.source_control.github_service import GitHubService
from repo_organizer.services.progress_reporter import ProgressReporter
from repo_organizer.utils.logger import Logger
from repo_organizer.utils.rate_limiter import RateLimiter
from repo_organizer.config.settings import load_settings

# Import adapter implementation for AnalyzerPort
from repo_organizer.infrastructure.analysis.langchain_claude_adapter import (
    LangChainClaudeAdapter,
)


class ApplicationFactory:
    """Factory for creating application instances.

    This class implements the Factory Method pattern, creating properly
    configured application instances with their dependencies.
    """

    @classmethod
    def create_application(
        cls,
        force_analysis: bool = False,
        output_dir: Optional[str] = None,
        max_repos: Optional[int] = None,
        debug_logging: Optional[bool] = None,
        env_file: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, Optional[str]], None]] = None,
        quiet_mode: bool = False,
    ) -> ApplicationRunner:
        """Create a fully configured application instance.

        Args:
            force_analysis: Whether to force re-analysis of repositories
            output_dir: Optional custom output directory
            max_repos: Optional maximum number of repositories to analyze
            debug_logging: Whether to enable debug logging
            env_file: Optional path to .env file
            progress_callback: Optional callback for progress reporting
            quiet_mode: Whether to minimize console output

        Returns:
            Configured ApplicationRunner instance
        """
        # Load settings
        settings = load_settings(env_file)

        # ------------------------------------------------------------------
        # Apply CLI / caller overrides
        # ------------------------------------------------------------------
        # A user supplied path may contain a leading "~" or environment
        # variables.  Make sure these are expanded so subsequent code that
        # relies on the directory (including the ApplicationRunner) does
        # not unexpectedly attempt to create folders like literally
        # "~/some/path".

        if output_dir:
            import os

            expanded_output = os.path.abspath(
                os.path.expanduser(os.path.expandvars(output_dir))
            )
            settings.output_dir = expanded_output

            # Create the directory *now* so that in the (unlikely) event of
            # a failure before the ApplicationRunner is instantiated we do
            # not lose analysis results because of a missing folder.
            os.makedirs(settings.output_dir, exist_ok=True)
        if max_repos:
            settings.max_repos = max_repos
        if debug_logging is not None:
            settings.debug_logging = debug_logging
        settings.quiet_mode = quiet_mode

        # Create console
        console = Console(quiet=quiet_mode)

        # Create logger
        import os
        import datetime

        # Use logs directory from settings
        logs_dir = settings.logs_dir
        os.makedirs(logs_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(logs_dir, f"analysis_log_{timestamp}.txt")
        logger = Logger(
            log_file,
            console,
            debug_enabled=settings.debug_logging,
            quiet_mode=quiet_mode,
        )

        # Create rate limiters
        github_limiter = RateLimiter(settings.github_rate_limit, name="GitHub")
        llm_limiter = RateLimiter(settings.llm_rate_limit, name="Claude LLM")

        # Create progress reporter
        progress_reporter = ProgressReporter()
        if progress_callback:
            progress_reporter.set_progress_callback(progress_callback)

        # Create services
        github_service = GitHubService(
            settings.github_username,
            settings.github_token,
            rate_limiter=github_limiter,
            logger=logger,
        )

        # Create analyzer using the LangChainClaudeAdapter (implements AnalyzerPort)
        analyzer = LangChainClaudeAdapter(
            api_key=settings.anthropic_api_key,
            model_name=settings.llm_model,
            temperature=settings.llm_temperature,
            thinking_enabled=settings.llm_thinking_enabled,
            thinking_budget=settings.llm_thinking_budget,
            rate_limiter=llm_limiter,
            logger=logger,
        )

        # Create application runner
        return ApplicationRunner(
            settings=settings,
            logger=logger,
            github_service=github_service,
            analyzer=analyzer,  # Pass the analyzer instead of llm_service
            progress_reporter=progress_reporter,
            github_limiter=github_limiter,
            llm_limiter=llm_limiter,
            force_analysis=force_analysis,
        )
