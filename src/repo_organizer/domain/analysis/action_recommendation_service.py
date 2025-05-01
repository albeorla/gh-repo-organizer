"""Domain service for generating action recommendations for repositories.

This service contains the business logic for determining what actions should be
taken for repositories based on their analysis results.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence

from repo_organizer.domain.analysis.events import (
    HighPriorityIssueIdentified,
    RepositoryActionRecommended,
)
from repo_organizer.domain.analysis.models import RepoAnalysis
from repo_organizer.domain.analysis.value_objects import (
    ActivityLevel,
    PriorityLevel,
    RecommendedAction,
    RepoAssessment,
    ValueLevel,
)
from repo_organizer.domain.core.events import event_bus
from repo_organizer.domain.source_control.models import Repository

logger = logging.getLogger(__name__)


class ActionRecommendationService:
    """Service for determining recommended actions for repositories.

    This pure domain service applies business rules to repository analyses to determine
    the most appropriate action (DELETE/ARCHIVE/EXTRACT/KEEP/PIN).
    """

    @staticmethod
    async def recommend_action(
        repo: Repository, analysis: RepoAnalysis,
    ) -> RecommendedAction:
        """Determine the recommended action for a repository based on its analysis.

        Args:
            repo: The repository being analyzed
            analysis: The analysis of the repository

        Returns:
            The recommended action (DELETE/ARCHIVE/EXTRACT/KEEP/PIN)
        """
        # Get a clean assessment of the repository
        assessment = RepoAssessment.from_strings(
            activity=analysis.activity_assessment,
            value=analysis.estimated_value,
            reasoning=analysis.action_reasoning,
        )

        # Apply business rules to determine the appropriate action
        action = ActionRecommendationService._apply_action_rules(
            repo, analysis, assessment,
        )
        reasoning = ActionRecommendationService._generate_reasoning(
            repo, analysis, assessment, action,
        )

        # Publish domain event for the recommended action
        await event_bus.dispatch(
            RepositoryActionRecommended(
                aggregate_id=repo.name,
                repo_name=repo.name,
                action=action.value,
                reasoning=reasoning,
            ),
        )

        # Check for high priority issues and publish events
        high_priority_recommendations = [
            r
            for r in analysis.recommendations
            if PriorityLevel.from_string(r.priority) == PriorityLevel.HIGH
        ]

        # Process high priority issues
        for recommendation in high_priority_recommendations:
            await event_bus.dispatch(
                HighPriorityIssueIdentified(
                    aggregate_id=repo.name, repo_name=repo.name, issue=recommendation,
                ),
            )

        return action

    @staticmethod
    def _apply_action_rules(
        repo: Repository, analysis: RepoAnalysis, assessment: RepoAssessment,
    ) -> RecommendedAction:
        """Apply business rules to determine the recommended action.

        Args:
            repo: The repository
            analysis: The analysis results
            assessment: The repository assessment

        Returns:
            The recommended action
        """
        # Check for existing recommended action
        if (
            hasattr(analysis, "recommended_action")
            and analysis.recommended_action
            and analysis.recommended_action != "KEEP"
        ):
            return RecommendedAction.from_string(analysis.recommended_action)

        # Default action is KEEP
        action = RecommendedAction.KEEP

        # Apply business rules
        if assessment.activity == ActivityLevel.INACTIVE:
            # Inactive repositories are candidates for archiving or deletion
            if assessment.value == ValueLevel.LOW:
                action = RecommendedAction.DELETE
            else:
                action = RecommendedAction.ARCHIVE

        elif assessment.activity == ActivityLevel.LOW:
            # Low activity repositories depend on value
            if assessment.value == ValueLevel.LOW:
                action = RecommendedAction.ARCHIVE
            elif assessment.value == ValueLevel.HIGH:
                # Low activity but high value - may need extraction
                if any(
                    "extract" in r.recommendation.lower()
                    for r in analysis.recommendations
                ):
                    action = RecommendedAction.EXTRACT
                else:
                    action = RecommendedAction.KEEP

        # High value repositories might be pinned if they're active
        if assessment.value == ValueLevel.HIGH:
            if assessment.activity in [ActivityLevel.MEDIUM, ActivityLevel.HIGH]:
                action = RecommendedAction.PIN
            elif assessment.activity == ActivityLevel.INACTIVE:
                action = RecommendedAction.ARCHIVE

        # Special case: already archived repositories
        if repo.is_archived:
            if assessment.value == ValueLevel.LOW:
                action = RecommendedAction.DELETE
            else:
                action = RecommendedAction.ARCHIVE  # keep it archived

        return action

    @staticmethod
    def _generate_reasoning(
        repo: Repository,
        analysis: RepoAnalysis,
        assessment: RepoAssessment,
        action: RecommendedAction,
    ) -> str:
        """Generate a reasoning string for the recommended action.

        Args:
            repo: The repository
            analysis: The analysis results
            assessment: The repository assessment
            action: The recommended action

        Returns:
            A string explaining the reasoning behind the action
        """
        # Use existing reasoning if available
        if (
            analysis.action_reasoning
            and analysis.action_reasoning != "No specific reasoning provided"
        ):
            return analysis.action_reasoning

        # Generate reasoning based on the action
        if action == RecommendedAction.DELETE:
            return (
                f"Repository has low value ({assessment.value.value}) and "
                f"{assessment.activity.value} activity. No significant code or documentation "
                f"worth preserving."
            )

        if action == RecommendedAction.ARCHIVE:
            return (
                f"Repository has {assessment.activity.value} activity but "
                f"{assessment.value.value} value. Should be preserved for reference but "
                f"not actively maintained."
            )

        if action == RecommendedAction.EXTRACT:
            return (
                f"Repository has valuable components that should be extracted before "
                f"archiving or deleting. Value: {assessment.value.value}, "
                f"Activity: {assessment.activity.value}."
            )

        if action == RecommendedAction.PIN:
            return (
                f"Repository has high value ({assessment.value.value}) and should be "
                f"pinned for visibility. Activity level: {assessment.activity.value}."
            )

        # KEEP
        return (
            f"Repository should be kept active with its current settings. "
            f"Value: {assessment.value.value}, Activity: {assessment.activity.value}."
        )

    @staticmethod
    async def batch_recommend_actions(
        repositories: Sequence[Repository], analyses: Sequence[RepoAnalysis],
    ) -> dict[str, RecommendedAction]:
        """Generate recommended actions for multiple repositories in parallel.

        Args:
            repositories: The repositories to analyze
            analyses: The analyses for each repository

        Returns:
            Dictionary mapping repository names to recommended actions
        """
        if len(repositories) != len(analyses):
            raise ValueError("Number of repositories and analyses must match")

        # Create a dictionary to store results
        results = {}

        # Create tasks for each recommendation
        tasks = []
        repo_map = {repo.name: repo for repo in repositories}

        for analysis in analyses:
            if analysis.repo_name in repo_map:
                repo = repo_map[analysis.repo_name]
                task = ActionRecommendationService.recommend_action(repo, analysis)
                tasks.append(task)

        # Run all tasks concurrently
        if tasks:
            try:
                recommendations = await asyncio.gather(*tasks, return_exceptions=True)

                # Map results to repository names
                for i, analysis in enumerate(analyses):
                    if i < len(recommendations):
                        # Skip exceptions
                        if isinstance(recommendations[i], Exception):
                            logger.error(
                                f"Error recommending action for {analysis.repo_name}: {recommendations[i]!s}",
                            )
                            continue
                        results[analysis.repo_name] = recommendations[i]
            except Exception as e:
                logger.error(f"Error during batch recommendation processing: {e!s}")

        return results

    @staticmethod
    def categorize_repositories(
        analyses: Sequence[RepoAnalysis],
    ) -> dict[RecommendedAction, list[RepoAnalysis]]:
        """Categorize repositories by their recommended action.

        Args:
            analyses: List of repository analyses

        Returns:
            Dictionary mapping actions to lists of analyses
        """
        categories: dict[RecommendedAction, list[RepoAnalysis]] = {
            action: [] for action in RecommendedAction
        }

        for analysis in analyses:
            action = RecommendedAction.from_string(analysis.recommended_action)
            categories[action].append(analysis)

        return categories
