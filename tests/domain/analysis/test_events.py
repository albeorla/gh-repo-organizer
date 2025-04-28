"""
Test cases for the standalone domain events in the analysis bounded context.
"""

import pytest
import uuid
from datetime import datetime

from repo_organizer.domain.analysis.events import (
    RepositoryAnalysisCompleted,
    RepositoryActionRecommended,
    HighPriorityIssueIdentified,
    AnalysisError,
)
from repo_organizer.domain.analysis.models import RepoAnalysis, Recommendation
from repo_organizer.domain.core.events import event_bus


# --- Fixtures ---
@pytest.fixture
def repo_analysis():
    return RepoAnalysis(
        repo_name="test-repo",
        summary="Test repo summary",
        strengths=["Good documentation", "CI/CD pipeline"],
        weaknesses=["Security issues", "Outdated dependencies"],
        estimated_value="HIGH",
        activity_assessment="MEDIUM",
        recommendations=[
            Recommendation(
                recommendation="Fix security issues",
                reason="Found security vulnerabilities",
                priority="HIGH",
            )
        ],
        tags=["security", "documentation"],
        recommended_action="KEEP",
        action_reasoning="Keep due to high value",
    )


# --- Tests ---
def test_repository_analysis_completed_event(repo_analysis):
    """Test creation and serialization of RepositoryAnalysisCompleted event."""
    event = RepositoryAnalysisCompleted(
        aggregate_id="test-repo", analysis=repo_analysis
    )

    assert isinstance(event.event_id, uuid.UUID)
    assert isinstance(event.timestamp, datetime)
    assert event.aggregate_id == "test-repo"
    assert event.analysis == repo_analysis

    event_dict = event.to_dict()
    assert event_dict["event_type"] == "RepositoryAnalysisCompleted"
    assert event_dict["aggregate_id"] == "test-repo"

    # Check event data
    data = event_dict["data"]
    assert data["repo_name"] == "test-repo"
    assert data["summary"] == "Test repo summary"
    assert data["value"] == "HIGH"
    assert data["activity"] == "MEDIUM"
    assert data["action"] == "KEEP"


def test_repository_action_recommended_event():
    """Test creation and serialization of RepositoryActionRecommended event."""
    event = RepositoryActionRecommended(
        aggregate_id="test-repo",
        repo_name="test-repo",
        action="ARCHIVE",
        reasoning="Low activity and medium value",
    )

    assert isinstance(event.event_id, uuid.UUID)
    assert event.aggregate_id == "test-repo"
    assert event.repo_name == "test-repo"
    assert event.action == "ARCHIVE"
    assert event.reasoning == "Low activity and medium value"

    event_dict = event.to_dict()
    assert event_dict["event_type"] == "RepositoryActionRecommended"
    data = event_dict["data"]
    assert data["repo_name"] == "test-repo"
    assert data["action"] == "ARCHIVE"
    assert data["reasoning"] == "Low activity and medium value"


def test_high_priority_issue_identified_event():
    """Test creation and serialization of HighPriorityIssueIdentified event."""
    issue = Recommendation(
        recommendation="Fix security issues",
        reason="Found security vulnerabilities",
        priority="HIGH",
    )

    event = HighPriorityIssueIdentified(
        aggregate_id="test-repo", repo_name="test-repo", issue=issue
    )

    assert isinstance(event.event_id, uuid.UUID)
    assert event.aggregate_id == "test-repo"
    assert event.repo_name == "test-repo"
    assert event.issue == issue

    event_dict = event.to_dict()
    assert event_dict["event_type"] == "HighPriorityIssueIdentified"
    data = event_dict["data"]
    assert data["repo_name"] == "test-repo"
    assert data["recommendation"] == "Fix security issues"
    assert data["reason"] == "Found security vulnerabilities"
    assert data["priority"] == "HIGH"


def test_analysis_error_event():
    """Test creation and serialization of AnalysisError event."""
    event = AnalysisError(
        aggregate_id="test-repo",
        repo_name="test-repo",
        error_message="Failed to retrieve repository data",
    )

    assert isinstance(event.event_id, uuid.UUID)
    assert event.aggregate_id == "test-repo"
    assert event.repo_name == "test-repo"
    assert event.error_message == "Failed to retrieve repository data"

    event_dict = event.to_dict()
    assert event_dict["event_type"] == "AnalysisError"
    data = event_dict["data"]
    assert data["repo_name"] == "test-repo"
    assert data["error"] == "Failed to retrieve repository data"


@pytest.mark.asyncio
async def test_event_handler_integration():
    """Test that events can be dispatched and handled via the event bus."""
    handler_called = {"value": False}

    async def test_handler(event):
        handler_called["value"] = True
        handler_called["event"] = event

    # Register handler
    event_bus.register(RepositoryAnalysisCompleted, test_handler)

    # Create and dispatch event
    repo_analysis = RepoAnalysis(
        repo_name="test-repo",
        summary="Test repo summary",
        strengths=["Good code quality"],
        weaknesses=["Limited scope"],
        estimated_value="HIGH",
        activity_assessment="MEDIUM",
        recommendations=[],
        tags=["test"],
        recommended_action="KEEP",
        action_reasoning="Keep due to high value",
    )

    event = RepositoryAnalysisCompleted(
        aggregate_id="test-repo", analysis=repo_analysis
    )

    await event_bus.dispatch(event)

    # Verify handler was called
    assert handler_called["value"] is True
    assert handler_called["event"] == event

    # Clean up
    event_bus.unregister(RepositoryAnalysisCompleted, test_handler)
