"""Domain service for orchestrating repository analysis.

This module contains the RepositoryAnalyzerService which coordinates the analysis
of repositories using the analyzer and source control ports.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from repo_organizer.domain.analysis.action_recommendation_service import (
    ActionRecommendationService,
)
from repo_organizer.domain.analysis.events import (
    AnalysisError,
    RepositoryAnalysisCompleted,
)
from repo_organizer.domain.core.events import event_bus

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from repo_organizer.domain.analysis.models import RepoAnalysis
    from repo_organizer.domain.analysis.protocols import AnalyzerPort
    from repo_organizer.domain.source_control.models import Repository
    from repo_organizer.domain.source_control.protocols import SourceControlPort

logger = logging.getLogger(__name__)


class RepositoryAnalyzerService:
    """Service that orchestrates repository analysis.

    This service coordinates between the source control port and analyzer port
    to analyze repositories and generate reports. It follows the Dependency Inversion
    Principle by depending on abstractions rather than concrete implementations.
    """

    def __init__(
        self,
        output_dir: str | Path,
        source_control_port: SourceControlPort,
        analyzer_port: AnalyzerPort,
        max_repos: int | None = None,
        debug: bool = False,
        repo_filter: Callable[[Repository], bool] | None = None,
        force_reanalyze: bool = False,
    ):
        """Initialize the repository analyzer service.

        Args:
            output_dir: Directory to write analysis reports to
            source_control_port: Port for interacting with source control
            analyzer_port: Port for analyzing repositories
            max_repos: Maximum number of repositories to analyze, or None for no limit
            debug: Whether to enable debug logging
            repo_filter: Optional filter function for repositories
            force_reanalyze: Whether to reanalyze repositories that already have reports
        """
        self.output_dir = Path(output_dir)
        self.source_control_port = source_control_port
        self.analyzer_port = analyzer_port
        self.max_repos = max_repos
        self.debug = debug
        self.repo_filter = repo_filter
        self.force_reanalyze = force_reanalyze

        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

        # Configure logging
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

    def should_analyze_repo(self, repo: Repository) -> bool:
        """Determine if a repository should be analyzed.

        Args:
            repo: The repository to check

        Returns:
            True if the repository should be analyzed
        """
        # Skip if filtered out
        if self.repo_filter and not self.repo_filter(repo):
            logger.debug(f"Skipping {repo.name} - filtered out")
            return False

        # Check if report already exists
        report_path = self.output_dir / f"{repo.name}.json"
        if report_path.exists() and not self.force_reanalyze:
            logger.debug(f"Skipping {repo.name} - report exists")
            return False

        return True

    async def analyze_repository(self, repo: Repository) -> RepoAnalysis | None:
        """Analyze a single repository.

        Args:
            repo: The repository to analyze

        Returns:
            The repository analysis if successful, None if analysis fails
        """
        try:
            logger.info(f"Analyzing repository: {repo.name}")

            # Fetch additional data
            languages = self.source_control_port.fetch_languages(repo)
            commits = self.source_control_port.recent_commits(repo, limit=20)
            contributors = self.source_control_port.contributors(repo)

            # Update repository with language data
            if languages and not repo.languages:
                repo = repo.with_languages(
                    {lb.language: lb.percentage for lb in languages},
                )

            # Prepare data for analysis
            data = self.prepare_analysis_data(repo, commits, contributors)

            # Run analysis
            analysis = self.analyzer_port.analyze(data)

            # Publish domain event
            await event_bus.dispatch(
                RepositoryAnalysisCompleted(aggregate_id=repo.name, analysis=analysis),
            )

            # Generate action recommendation
            action_service = ActionRecommendationService()
            await action_service.recommend_action(repo, analysis)

            # Write report
            await self.write_report(repo.name, analysis)

            return analysis

        except Exception as e:
            error_msg = f"Error analyzing {repo.name}: {e!s}"
            logger.error(error_msg)

            # Publish error event
            await event_bus.dispatch(
                AnalysisError(
                    aggregate_id=repo.name,
                    repo_name=repo.name,
                    error_message=error_msg,
                ),
            )

            if self.debug:
                logger.exception(e)

            return None

    def prepare_analysis_data(
        self,
        repo: Repository,
        commits: Sequence[Any],
        contributors: Sequence[Any],
    ) -> dict[str, Any]:
        """Prepare repository data for analysis.

        Args:
            repo: The repository to prepare data for
            commits: Recent commits
            contributors: Repository contributors

        Returns:
            Dictionary of data for analysis
        """
        # Prepare repository data
        data: dict[str, Any] = {
            "name": repo.name,
            "description": repo.description or "",
            "url": repo.url or "",
            "updated_at": repo.updated_at or "",
            "is_archived": repo.is_archived,
            "stars": repo.stars,
            "forks": repo.forks,
        }

        # Add language data if available
        if repo.languages:
            data["languages"] = {lb.language: lb.percentage for lb in repo.languages}

        # Add commit data
        if commits:
            data["commits"] = [
                {
                    "hash": commit.hash,
                    "message": commit.message,
                    "author": commit.author,
                    "date": commit.date,
                }
                for commit in commits
            ]

        # Add contributor data
        if contributors:
            data["contributors"] = [
                {
                    "name": contributor.name,
                    "commits": contributor.commits,
                }
                for contributor in contributors
            ]

        return data

    async def write_report(self, repo_name: str, analysis: RepoAnalysis) -> None:
        """Write an analysis report to disk.

        Args:
            repo_name: Name of the repository
            analysis: The analysis to write
        """
        report_path = self.output_dir / f"{repo_name}.json"

        # Convert to dictionary
        pydantic_model = analysis.to_pydantic()
        report_data = pydantic_model.model_dump()

        # Write to file
        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)

        logger.debug(f"Wrote report to {report_path}")

    async def generate_reports(self, repos: Sequence[Repository]) -> list[RepoAnalysis]:
        """Generate analysis reports for multiple repositories.

        Args:
            repos: The repositories to analyze

        Returns:
            List of successful analyses
        """
        analyses = []
        count = 0
        tasks = []

        for repo in repos:
            # Check max repos limit
            if self.max_repos and count >= self.max_repos:
                logger.info(f"Reached max repos limit of {self.max_repos}")
                break

            # Check if repo should be analyzed
            if not self.should_analyze_repo(repo):
                continue

            # Analyze repo (create task)
            tasks.append(self.analyze_repository(repo))
            count += 1

        # Run all analyses in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Analysis failed with exception: {result}")
            elif result is not None:
                analyses.append(result)

        return analyses
