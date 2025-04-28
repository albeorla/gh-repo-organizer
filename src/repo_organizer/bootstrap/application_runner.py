"""
Main application orchestrator for the GitHub Repository Organizer.

This module contains the ApplicationRunner class which serves as the main
orchestrator for the repository analysis process, following the Façade pattern
to provide a simple interface to the complex subsystem of services.
"""

import os
import time
import concurrent.futures
import sys
from threading import Lock
from typing import Any, Dict

from rich.console import Console

from repo_organizer.services.repository_analyzer_service import (
    RepositoryAnalyzerService,
)


class ApplicationRunner:
    """Main application orchestrator.

    This class serves as a Façade, providing a simpler interface to the complex
    subsystem of services for repository analysis.
    """

    def __init__(
        self,
        settings,
        logger,
        github_service,
        analyzer,  # Changed parameter from llm_service to analyzer
        progress_reporter,
        github_limiter,
        llm_limiter,
        force_analysis=False,
    ):
        """Initialize the application runner with dependencies.

        This constructor follows the Dependency Injection pattern,
        allowing for better testability and separation of concerns.

        Args:
            settings: Application settings
            logger: Logger instance
            github_service: GitHub service instance
            analyzer: AnalyzerPort implementation for repository analysis
            progress_reporter: Progress reporter instance
            github_limiter: GitHub rate limiter
            llm_limiter: LLM rate limiter
            force_analysis: Whether to force re-analysis of repositories
        """
        # Store dependencies
        self.settings = settings
        self.logger = logger
        self.github_service = github_service
        self.analyzer = analyzer  # Using analyzer (AnalyzerPort) instead of llm_service
        self.progress_reporter = progress_reporter
        self.github_limiter = github_limiter
        self.llm_limiter = llm_limiter

        # Store configuration
        self.force_analysis = force_analysis
        self.output_dir = settings.output_dir
        self.max_repos = settings.max_repos
        self.max_workers = settings.max_workers
        self.debug_logging = settings.debug_logging

        # Internal state
        self.console = Console()
        self.progress_lock = Lock()
        self.completed = 0
        self.errors = 0
        self.start_time = time.time()

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        # Log if forcing analysis
        if self.force_analysis:
            self.logger.log(
                "Force analysis enabled: Cache checks will be bypassed.",
                level="warning",
            )

    def _should_skip_analysis(self, repo_info: Dict[str, Any]) -> bool:
        """Check if analysis for a repo should be skipped based on existing report file.

        Args:
            repo_info: Repository information dictionary

        Returns:
            True if analysis should be skipped, False otherwise
        """
        # Check force flag first
        if self.force_analysis:
            return False  # Always analyze if force flag is set

        repo_name = repo_info.get("name")
        if not repo_name:
            return False  # Cannot check without a name

        # Skip if a report exists *and* it is newer than or equal to the
        # repository's last update timestamp.  This prevents stale reports
        # from lingering forever while still avoiding needless re-analysis.
        repo_file_path = os.path.join(self.output_dir, f"{repo_name}.md")
        if os.path.exists(repo_file_path):
            try:
                updated_at_str = repo_info.get("updatedAt") or repo_info.get(
                    "updated_at"
                )
                if updated_at_str:
                    import datetime as _dt

                    # Remove a trailing "Z" if present to satisfy fromisoformat.
                    updated_at_str = updated_at_str.rstrip("Z")
                    repo_updated_ts = _dt.datetime.fromisoformat(updated_at_str)
                    report_mtime_ts = _dt.datetime.fromtimestamp(
                        os.path.getmtime(repo_file_path)
                    )

                    if report_mtime_ts >= repo_updated_ts:
                        self.logger.log(
                            f"Skipping analysis for {repo_name} (cached report up-to-date)",
                            level="info",
                        )
                        return True
            except Exception as _sk_err:  # pragma: no cover – best-effort parsing
                # On any parsing error fall back to the old behaviour (skip).
                self.logger.log(
                    f"Could not validate freshness of report for {repo_name}: {_sk_err}",
                    level="debug",
                )
                return True

        return False

    def analyze_repo_task(self, repo, repository_analyzer, pbar):
        """Task function for parallel repository analysis.

        Args:
            repo: Repository information dictionary
            repository_analyzer: Repository analyzer service
            pbar: progress tracker for overall progress

        Returns:
            Repository analysis result or None if failed
        """
        repo_name = repo.get("name", "unknown_repo")
        analysis = None
        success = False

        self.logger.log(f"Analyzing repository: {repo_name}", level="info")

        try:
            # Analyze the repository - rate limiting is handled inside the service
            analysis = repository_analyzer.analyze_repository(repo)
            if (
                analysis and "error" not in analysis.tags
            ):  # Check if analysis didn't return placeholder
                self.logger.log(f"Successfully analyzed: {repo_name}", level="debug")
                success = True
            else:
                self.logger.log(
                    f"Analysis completed with errors for repo: {repo_name}",
                    level="warning",
                )
        except Exception as e:
            # Log exception caught directly within the task
            self.logger.log(
                f"Exception in analyze_repo_task for {repo_name}: {type(e).__name__}: {str(e)}",
                level="error",
            )
            import traceback

            self.logger.log(
                f"Traceback (analyze_repo_task for {repo_name}):\n{traceback.format_exc()}",
                level="debug",
            )
            # Note: success remains False
        finally:
            with self.progress_lock:
                if success:
                    self.completed += 1
                else:
                    self.errors += 1

                # Update progress
                if pbar:
                    pbar.update(1)
                    # Update status description
                    new_desc = f"Analyzed: {self.completed}, Failed: {self.errors}"
                    pbar.set_description(new_desc)

        return analysis

    def get_output_dir(self) -> str:
        """Get the output directory.

        Returns:
            Output directory path
        """
        return self.output_dir

    def get_total_repos(self) -> int:
        """Get the total number of repositories that will be analyzed.

        Returns:
            Number of repositories to analyze
        """
        try:
            repos = self.github_service.get_repos(self.max_repos)
            filtered_repos = [r for r in repos if not self._should_skip_analysis(r)]
            return len(filtered_repos)
        except Exception as e:
            self.logger.log(f"Error determining repository count: {str(e)}", "error")
            return 0

    def get_summary(self) -> str:
        """Get a summary of the analysis results.

        Returns:
            Summary text for display
        """
        stats = self.logger.stats
        duration = time.time() - stats["start_time"] if "start_time" in stats else 0

        return (
            f"Duration: {duration:.2f} seconds\n"
            f"Repositories Analyzed: {stats.get('repos_analyzed', 0)}\n"
            f"Analysis Failures: {stats.get('repos_failed', 0)}\n"
            f"Repositories Skipped: {stats.get('repos_skipped', 0)}\n"
            f"API Retries: {stats.get('retries', 0)}"
        )

    def run(self, progress_callback=None):
        """Run the repository analysis process.

        This method coordinates the overall repository analysis workflow,
        using the Repository Analyzer Service to process each repository.
        It follows the Command pattern by encapsulating and executing the
        entire repository analysis process.

        Args:
            progress_callback: Optional callback function to report progress

        Returns:
            Dictionary with analysis results
        """
        # Set progress callback if provided
        if progress_callback:
            self.progress_reporter.set_progress_callback(progress_callback)
        self.logger.log(
            f"Starting GitHub repository analysis with {self.max_workers} workers"
        )
        if self.debug_logging:
            self.logger.log("Debug logging enabled", level="debug")
        self.logger.log(
            f"GitHub API rate limit: {self.github_limiter.calls_per_minute} calls/min"
        )
        self.logger.log(
            f"LLM API rate limit: {self.llm_limiter.calls_per_minute} calls/min"
        )

        # Create the analyzer service instance using our analyzer that implements AnalyzerPort
        repository_analyzer = RepositoryAnalyzerService(
            self.output_dir,
            self.settings.anthropic_api_key,
            self.github_service,
            analyzer=self.analyzer,  # Pass the analyzer instead of llm_service
            max_repos=self.max_repos,
            debug=self.debug_logging,
            repo_filter=None,
            force_reanalyze=self.force_analysis,
            logger=self.logger,  # Pass the logger to avoid creating a new one
        )

        # Get repositories
        try:
            self.logger.log("Fetching up to 100 repositories from GitHub...")
            repos = self.github_service.get_repos(self.max_repos)
            if not repos:
                self.logger.log("No repositories found to analyze.", level="warning")
                return
            self.logger.log(f"Successfully fetched {len(repos)} repositories")
        except Exception as e:
            self.logger.log(f"Failed to fetch repositories: {str(e)}", level="error")
            sys.exit(1)  # Exit if we can't fetch repos

        # Analyze repositories
        self.logger.log(f"Analyzing or checking cache for {len(repos)} repositories...")
        analyses = []

        # Reset progress counters for this run
        self.completed = 0
        self.errors = 0
        self.logger.stats["repos_skipped"] = 0  # Ensure skipped count is reset

        # Create a custom progress tracker using the progress_callback
        class ProgressTracker:
            def __init__(self, total, callback):
                self.total = total
                self.callback = callback
                self.completed = 0

            def update(self, n=1):
                self.completed += n
                if self.callback:
                    # Keep status text short to prevent wrapping
                    status_text = f"{self.completed}/{self.total} completed"
                    self.callback(self.completed, self.total, status_text)

            def set_description(self, desc):
                if self.callback:
                    # Truncate long descriptions to prevent line wrapping
                    max_desc_len = 50
                    if len(desc) > max_desc_len:
                        desc = desc[:max_desc_len] + "..."
                    self.callback(self.completed, self.total, desc)

            def refresh(self):
                if self.callback:
                    self.callback(self.completed, self.total, None)

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            future_to_repo = {}
            skipped_count = 0

            # Create progress tracker if callback provided, otherwise None
            pbar = (
                ProgressTracker(len(repos), progress_callback)
                if progress_callback
                else None
            )

            for repo in repos:
                repo_name = repo.get("name")
                if not repo_name:
                    self.logger.log("Skipping repository with no name.", "warning")
                    skipped_count += 1
                    continue

                # Check if we should skip based on cache
                if self._should_skip_analysis(repo):
                    self.logger.log(
                        f"Skipping analysis for {repo_name} (cached result is up-to-date)",
                        level="info",
                    )
                    self.logger.update_stats("repos_skipped")
                    skipped_count += 1
                    continue  # Skip submitting this repo

                # If not skipped, submit the analysis task
                future_to_repo[
                    executor.submit(
                        self.analyze_repo_task, repo, repository_analyzer, pbar
                    )
                ] = repo

            # Update pbar total for skipped items
            if pbar:
                pbar.total = len(repos) - skipped_count
                pbar.refresh()

            # Process completed futures
            for future in concurrent.futures.as_completed(future_to_repo):
                repo_info = future_to_repo[future]
                repo_name = repo_info.get("name", "unknown")
                try:
                    analysis_result = future.result()
                    if analysis_result:
                        analyses.append(analysis_result)
                        # Write the individual report immediately after successful analysis
                        repository_analyzer._write_single_report(
                            analysis_result, repo_info
                        )
                except Exception as exc:
                    self.logger.log(
                        f"Error processing future for repo {repo_name}: {exc}",
                        level="error",
                    )

        # Generate final summary report only
        if analyses:
            valid_analyses = [a for a in analyses if "error" not in a.tags]
            repository_analyzer.generate_report(repos, valid_analyses)
        else:
            self.logger.log(
                "No valid analyses were completed to generate a summary report.",
                level="warning",
            )

        # Print summary statistics
        total_time = time.time() - self.start_time
        self.logger.log(f"Analysis complete in {total_time:.2f}s.", "success")
        if analyses:
            self.logger.log(f"Reports generated in {self.output_dir}", "success")
            self.logger.log(
                f"Main report: {os.path.join(self.output_dir, 'repositories_report.md')}"
            )

        self.logger.print_summary([self.github_limiter, self.llm_limiter])

        # Return result dictionary
        return {
            "output_dir": self.output_dir,
            "analyzed_count": len(analyses),
            "valid_analyses": len([a for a in analyses if "error" not in a.tags]),
            "total_time": total_time,
        }
