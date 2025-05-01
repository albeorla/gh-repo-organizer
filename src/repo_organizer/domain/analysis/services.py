"""Domain services for the analysis bounded context.

This module contains pure domain logic for evaluating repository activity and value.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from repo_organizer.domain.analysis.events import RepositoryAnalysisCompleted
from repo_organizer.domain.analysis.value_objects import (
    ActivityLevel,
    RecommendedAction,
    ValueLevel,
)
from repo_organizer.domain.core.events import event_bus

if TYPE_CHECKING:
    from collections.abc import Sequence

    from repo_organizer.domain.analysis.models import Recommendation, RepoAnalysis
    from repo_organizer.domain.source_control.models import Commit, Contributor, Repository

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service containing pure domain logic for repository analysis and evaluation.

    This is a stateless domain service that contains business logic for evaluating
    repository activity, determining value, and filtering recommendations.
    """

    @staticmethod
    def get_high_priority_recommendations(
        analysis: RepoAnalysis,
    ) -> Sequence[Recommendation]:
        """Extract only high priority recommendations from an analysis.

        Args:
            analysis: A repository analysis

        Returns:
            A sequence of high priority recommendations
        """
        return [r for r in analysis.recommendations if r.priority.lower() == "high"]

    @staticmethod
    def should_be_archived(analysis: RepoAnalysis) -> bool:
        """Determine if a repository should be archived based on analysis.

        The decision is based on the recommended_action if available, otherwise
        it's determined by the activity level and estimated value.

        Args:
            analysis: A repository analysis

        Returns:
            True if the repository should be archived, False otherwise
        """
        return analysis.recommended_action == RecommendedAction.ARCHIVE.value

    @staticmethod
    def should_be_deleted(analysis: RepoAnalysis) -> bool:
        """Determine if a repository should be deleted based on analysis.

        Args:
            analysis: A repository analysis

        Returns:
            True if the repository should be deleted, False otherwise
        """
        return analysis.recommended_action == RecommendedAction.DELETE.value

    @staticmethod
    def should_be_pinned(analysis: RepoAnalysis) -> bool:
        """Determine if a repository should be pinned based on analysis.

        Args:
            analysis: A repository analysis

        Returns:
            True if the repository should be pinned, False otherwise
        """
        return analysis.recommended_action == RecommendedAction.PIN.value

    @staticmethod
    def should_extract_value(analysis: RepoAnalysis) -> bool:
        """Determine if valuable parts should be extracted from repository before archiving/deleting.

        Args:
            analysis: A repository analysis

        Returns:
            True if the repository has valuable parts that should be extracted
        """
        return analysis.recommended_action == RecommendedAction.EXTRACT.value

    @staticmethod
    def evaluate_activity(
        repo: Repository,
        commits: Sequence[Commit],
        contributors: Sequence[Contributor],
    ) -> ActivityLevel:
        """Evaluate the activity level of a repository based on commits and contributors.

        Args:
            repo: The repository
            commits: Recent commits
            contributors: Contributors

        Returns:
            Activity level assessment
        """
        # Simple heuristic-based activity assessment
        # Could be enhanced with more sophisticated algorithm

        # Check if archived already
        if repo.is_archived:
            return ActivityLevel.INACTIVE

        # Check for recent commits
        if not commits:
            return ActivityLevel.INACTIVE

        # Check number of contributors
        if len(contributors) > 5:
            return ActivityLevel.HIGH

        # Check number of commits
        if len(commits) > 20:
            return ActivityLevel.HIGH
        if len(commits) > 5:
            return ActivityLevel.MEDIUM
        return ActivityLevel.LOW

    @staticmethod
    def evaluate_value(
        repo: Repository,
        languages: Sequence[str] | None = None,
        stars: int | None = None,
        forks: int | None = None,
    ) -> ValueLevel:
        """Evaluate the value/importance of a repository.

        Args:
            repo: The repository
            languages: Programming languages used
            stars: Number of stars (if not in repo)
            forks: Number of forks (if not in repo)

        Returns:
            Value level assessment
        """
        # Use repo values if not provided separately
        stars = stars if stars is not None else repo.stars
        forks = forks if forks is not None else repo.forks

        # High value indicators
        if stars > 10 or forks > 5:
            return ValueLevel.HIGH

        # Medium value indicators
        if stars > 3 or forks > 1:
            return ValueLevel.MEDIUM

        # Default to low value
        return ValueLevel.LOW

    @staticmethod
    async def analyze_repositories(
        repositories: Sequence[Repository],
        analyzer_port,  # Using Protocol type
        include_commits: bool = True,
        include_contributors: bool = True,
    ) -> list[RepoAnalysis]:
        """Analyze multiple repositories and generate assessments.

        Args:
            repositories: Repositories to analyze
            analyzer_port: Implementation of AnalyzerPort protocol
            include_commits: Whether to include commit data
            include_contributors: Whether to include contributor data

        Returns:
            List of repository analyses
        """
        analyses = []

        for repo in repositories:
            try:
                # Prepare data for analysis
                repo_data = {
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
                    repo_data["languages"] = {lb.language: lb.percentage for lb in repo.languages}

                # Perform analysis
                analysis = analyzer_port.analyze(repo_data)

                # Publish domain event
                await event_bus.dispatch(
                    RepositoryAnalysisCompleted(
                        aggregate_id=repo.name,
                        analysis=analysis,
                    ),
                )

                analyses.append(analysis)

            except Exception as e:
                logger.error(f"Error analyzing repository {repo.name}: {e!s}")

        return analyses

    @staticmethod
    def filter_by_tag(analyses: Sequence[RepoAnalysis], tag: str) -> list[RepoAnalysis]:
        """Filter analyses by a specific tag.

        Args:
            analyses: Sequence of analyses
            tag: Tag to filter by

        Returns:
            List of analyses with the specified tag
        """
        return [
            analysis for analysis in analyses if tag.lower() in [t.lower() for t in analysis.tags]
        ]

    @staticmethod
    def filter_by_value(
        analyses: Sequence[RepoAnalysis],
        min_value: ValueLevel = ValueLevel.LOW,
    ) -> list[RepoAnalysis]:
        """Filter analyses by minimum value level.

        Args:
            analyses: Sequence of analyses
            min_value: Minimum value level

        Returns:
            List of analyses with at least the specified value
        """
        value_levels = {
            ValueLevel.LOW: 0,
            ValueLevel.MEDIUM: 1,
            ValueLevel.HIGH: 2,
        }

        min_value_level = value_levels[min_value]

        return [
            analysis
            for analysis in analyses
            if value_levels[ValueLevel.from_string(analysis.estimated_value)] >= min_value_level
        ]

    @staticmethod
    def categorize_by_action(
        analyses: Sequence[RepoAnalysis],
    ) -> dict[str, list[RepoAnalysis]]:
        """Categorize analyses by their recommended action.

        Args:
            analyses: A sequence of repository analyses

        Returns:
            Dictionary mapping action types to lists of analyses
        """
        result = {action.value: [] for action in RecommendedAction}

        for analysis in analyses:
            action = analysis.recommended_action
            if action in result:
                result[action].append(analysis)
            else:
                # Default to KEEP for any unknown actions
                result[RecommendedAction.KEEP.value].append(analysis)

        return result
