"""
Domain services for the analysis bounded context.

This module contains pure domain logic for working with repository analyses.
"""

from __future__ import annotations

from typing import Sequence

from repo_organizer.domain.analysis.models import RepoAnalysis, Recommendation


class AnalysisService:
    """
    Service containing pure domain logic for working with repository analyses.

    This is a stateless domain service that contains business logic for working
    with RepoAnalysis objects.
    """

    @staticmethod
    def get_high_priority_recommendations(
        analysis: RepoAnalysis,
    ) -> Sequence[Recommendation]:
        """
        Extract only high priority recommendations from an analysis.

        Args:
            analysis: A repository analysis

        Returns:
            A sequence of high priority recommendations
        """
        return [r for r in analysis.recommendations if r.priority.lower() == "high"]

    @staticmethod
    def should_be_archived(analysis: RepoAnalysis) -> bool:
        """
        Determine if a repository should be archived based on analysis.

        The decision is based on the recommended_action if available, otherwise
        it's determined by the activity level and estimated value.

        Args:
            analysis: A repository analysis

        Returns:
            True if the repository should be archived, False otherwise
        """
        # If the model has the recommended_action field and it's set to ARCHIVE
        if (
            hasattr(analysis, "recommended_action")
            and analysis.recommended_action == "ARCHIVE"
        ):
            return True

        # Otherwise use a heuristic based on activity and value
        activity_low = (
            hasattr(analysis, "activity_assessment")
            and "low" in analysis.activity_assessment.lower()
        )
        value_low = (
            hasattr(analysis, "estimated_value")
            and analysis.estimated_value.lower() == "low"
        )

        return activity_low and value_low

    @staticmethod
    def should_be_deleted(analysis: RepoAnalysis) -> bool:
        """
        Determine if a repository should be deleted based on analysis.

        Args:
            analysis: A repository analysis

        Returns:
            True if the repository should be deleted, False otherwise
        """
        # Check for explicit DELETE recommendation
        if (
            hasattr(analysis, "recommended_action")
            and analysis.recommended_action == "DELETE"
        ):
            return True

        return False

    @staticmethod
    def is_pinned(analysis: RepoAnalysis) -> bool:
        """
        Determine if a repository should be pinned based on analysis.

        Args:
            analysis: A repository analysis

        Returns:
            True if the repository should be pinned, False otherwise
        """
        # Check for explicit PIN recommendation
        if (
            hasattr(analysis, "recommended_action")
            and analysis.recommended_action == "PIN"
        ):
            return True

        # Also pin high value repositories
        return (
            hasattr(analysis, "estimated_value")
            and analysis.estimated_value.lower() == "high"
        )
