"""
Unit tests for the ActionRecommendationService.
"""

import pytest
from unittest.mock import MagicMock, patch

from repo_organizer.domain.analysis.action_recommendation_service import (
    ActionRecommendationService,
)
from repo_organizer.domain.analysis.models import RepoAnalysis, Recommendation
from repo_organizer.domain.analysis.value_objects import RecommendedAction
from repo_organizer.domain.core.events import event_bus
from repo_organizer.domain.source_control.models import Repository


class TestActionRecommendationService:
    """Test suite for the ActionRecommendationService."""

    @pytest.fixture
    def mock_event_bus(self, monkeypatch):
        """Mock the event bus to avoid actually dispatching events."""

        # Create a coroutine function mock
        async def mock_dispatch_coro(*args, **kwargs):
            return None

        mock_dispatch = MagicMock()
        # Make the mock return a coroutine when called
        mock_dispatch.side_effect = mock_dispatch_coro

        monkeypatch.setattr(event_bus, "dispatch", mock_dispatch)
        return mock_dispatch

    @pytest.fixture
    def inactive_repo(self):
        """Create an inactive repository with low value."""
        return Repository(
            name="inactive-repo",
            description="An inactive repository",
            url="https://github.com/user/inactive-repo",
            updated_at="2020-01-01T00:00:00Z",  # Old update date
            is_archived=False,
            stars=0,
            forks=0,
        )

    @pytest.fixture
    def inactive_analysis(self):
        """Create an analysis for an inactive repository with low value."""
        return RepoAnalysis(
            repo_name="inactive-repo",
            summary="This repository is inactive and has low value.",
            strengths=["Has basic documentation"],
            weaknesses=["No recent commits", "No active contributors"],
            recommendations=[
                Recommendation(
                    recommendation="Delete repository",
                    reason="Inactive with no value",
                    priority="high",
                )
            ],
            activity_assessment="inactive",
            estimated_value="low",
            tags=["inactive", "low-value"],
        )

    @pytest.fixture
    def valuable_repo(self):
        """Create a valuable but inactive repository."""
        return Repository(
            name="valuable-inactive",
            description="A valuable but inactive repository",
            url="https://github.com/user/valuable-inactive",
            updated_at="2020-01-01T00:00:00Z",  # Old update date
            is_archived=False,
            stars=15,  # High stars
            forks=8,  # High forks
        )

    @pytest.fixture
    def valuable_analysis(self):
        """Create an analysis for a valuable but inactive repository."""
        return RepoAnalysis(
            repo_name="valuable-inactive",
            summary="This repository is inactive but has high value.",
            strengths=["Well documented", "Useful utility functions"],
            weaknesses=["No recent commits", "No active maintenance"],
            recommendations=[
                Recommendation(
                    recommendation="Archive repository",
                    reason="Inactive but valuable for reference",
                    priority="medium",
                )
            ],
            activity_assessment="inactive",
            estimated_value="high",
            tags=["inactive", "high-value"],
        )

    @pytest.mark.asyncio
    async def test_recommend_delete_for_inactive_low_value(
        self, inactive_repo, inactive_analysis, mock_event_bus
    ):
        """Test that an inactive repository with low value gets DELETE recommendation."""
        # Act
        action = await ActionRecommendationService.recommend_action(
            inactive_repo, inactive_analysis
        )

        # Assert
        assert action == RecommendedAction.DELETE
        assert mock_event_bus.called  # Event was dispatched

    @pytest.mark.asyncio
    async def test_recommend_archive_for_inactive_high_value(
        self, valuable_repo, valuable_analysis, mock_event_bus
    ):
        """Test that an inactive repository with high value gets ARCHIVE recommendation."""
        # Act
        action = await ActionRecommendationService.recommend_action(
            valuable_repo, valuable_analysis
        )

        # Assert
        assert action == RecommendedAction.ARCHIVE
        assert mock_event_bus.called  # Event was dispatched

    @pytest.mark.asyncio
    async def test_respect_explicit_recommendation(self, mock_event_bus):
        """Test that the service respects explicit recommendations in the analysis."""
        # Arrange
        repo = Repository(
            name="explicit-recommendation",
            description="Repository with explicit recommendation",
            url="https://github.com/user/explicit",
            updated_at="2023-01-01T00:00:00Z",
            is_archived=False,
            stars=2,
            forks=1,
        )

        analysis = RepoAnalysis(
            repo_name="explicit-recommendation",
            summary="This repository has an explicit recommendation",
            strengths=["Good code quality"],
            weaknesses=["Limited scope"],
            recommendations=[],
            activity_assessment="medium",
            estimated_value="medium",
            tags=["medium-value"],
            recommended_action="PIN",  # Explicit recommendation
            action_reasoning="Strategic importance",
        )

        # Act
        action = await ActionRecommendationService.recommend_action(repo, analysis)

        # Assert
        assert action == RecommendedAction.PIN
        assert mock_event_bus.called  # Event was dispatched

    @pytest.mark.asyncio
    async def test_batch_recommend_actions(self, mock_event_bus):
        """Test batch recommendations for multiple repositories."""
        # Arrange
        repos = [
            Repository(
                name="repo1",
                description="Repository 1",
                url="https://github.com/user/repo1",
                updated_at="2023-01-01T00:00:00Z",
                is_archived=False,
                stars=0,
                forks=0,
            ),
            Repository(
                name="repo2",
                description="Repository 2",
                url="https://github.com/user/repo2",
                updated_at="2023-01-01T00:00:00Z",
                is_archived=True,  # Archived
                stars=5,
                forks=2,
            ),
        ]

        analyses = [
            RepoAnalysis(
                repo_name="repo1",
                summary="Repository 1 summary",
                strengths=["Good tests"],
                weaknesses=["Limited documentation"],
                recommendations=[],
                activity_assessment="low",
                estimated_value="low",
                tags=["low-value"],
            ),
            RepoAnalysis(
                repo_name="repo2",
                summary="Repository 2 summary",
                strengths=["Well documented"],
                weaknesses=["Outdated"],
                recommendations=[],
                activity_assessment="inactive",
                estimated_value="medium",
                tags=["archived", "medium-value"],
            ),
        ]

        # Act
        results = await ActionRecommendationService.batch_recommend_actions(
            repos, analyses
        )

        # Assert
        assert len(results) == 2
        assert results["repo1"] == RecommendedAction.ARCHIVE  # Low activity, low value
        assert (
            results["repo2"] == RecommendedAction.ARCHIVE
        )  # Already archived, medium value

    @pytest.mark.asyncio
    async def test_batch_recommend_actions_with_error(self, mock_event_bus):
        """Test batch recommendations with an error in one repository."""
        # Arrange
        repos = [
            Repository(
                name="normal-repo",
                description="Normal repository",
                url="https://github.com/user/normal-repo",
                updated_at="2023-01-01T00:00:00Z",
                is_archived=False,
                stars=5,
                forks=2,
            ),
            Repository(
                name="error-repo",
                description="Repository that will trigger an error",
                url="https://github.com/user/error-repo",
                updated_at="2023-01-01T00:00:00Z",
                is_archived=False,
                stars=1,
                forks=0,
            ),
        ]

        analyses = [
            RepoAnalysis(
                repo_name="normal-repo",
                summary="Normal repository summary",
                strengths=["Good code"],
                weaknesses=[],
                recommendations=[],
                activity_assessment="high",
                estimated_value="medium",
                tags=["normal"],
            ),
            RepoAnalysis(
                repo_name="error-repo",
                summary="Error repository summary",
                strengths=[],
                weaknesses=["Contains error"],
                recommendations=[],
                activity_assessment="low",
                estimated_value="low",
                tags=["error"],
            ),
        ]

        # Create a patched version of recommend_action that fails for the error repo
        original_recommend_action = ActionRecommendationService.recommend_action

        async def mock_recommend_action(repo, analysis):
            if repo.name == "error-repo":
                raise ValueError("Test error")
            return await original_recommend_action(repo, analysis)

        # Apply patch
        with patch.object(
            ActionRecommendationService,
            "recommend_action",
            side_effect=mock_recommend_action,
        ):
            # Act
            results = await ActionRecommendationService.batch_recommend_actions(
                repos, analyses
            )

            # Assert
            assert len(results) == 1  # Only the successful repo
            assert "normal-repo" in results
            assert "error-repo" not in results
