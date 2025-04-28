"""
Domain events for the Analysis bounded context.

These events represent significant state changes and actions within the analysis process.
"""

from dataclasses import dataclass
import uuid
from datetime import datetime, UTC
from typing import Dict, Any

from repo_organizer.domain.analysis.models import RepoAnalysis, Recommendation

# Since we're having inheritance issues with the DomainEvent class,
# we'll create standalone event classes that follow the same pattern
# but don't inherit from DomainEvent.


@dataclass(frozen=True)
class RepositoryAnalysisCompleted:
    """Event fired when a repository analysis has been completed."""

    aggregate_id: str
    analysis: RepoAnalysis
    event_id: uuid.UUID = uuid.uuid4()
    timestamp: datetime = datetime.now(UTC)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation for serialization."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.__class__.__name__,
            "timestamp": self.timestamp.isoformat(),
            "aggregate_id": self.aggregate_id,
            "data": self._get_event_data(),
        }

    def _get_event_data(self) -> Dict[str, Any]:
        """Extract event-specific data for serialization."""
        return {
            "repo_name": self.analysis.repo_name,
            "summary": self.analysis.summary,
            "action": self.analysis.recommended_action,
            "value": self.analysis.estimated_value,
            "activity": self.analysis.activity_assessment,
        }


@dataclass(frozen=True)
class RepositoryActionRecommended:
    """Event fired when a specific action is recommended for a repository."""

    aggregate_id: str
    repo_name: str
    action: str  # DELETE/ARCHIVE/EXTRACT/KEEP/PIN
    reasoning: str
    event_id: uuid.UUID = uuid.uuid4()
    timestamp: datetime = datetime.now(UTC)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation for serialization."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.__class__.__name__,
            "timestamp": self.timestamp.isoformat(),
            "aggregate_id": self.aggregate_id,
            "data": self._get_event_data(),
        }

    def _get_event_data(self) -> Dict[str, Any]:
        """Extract event-specific data for serialization."""
        return {
            "repo_name": self.repo_name,
            "action": self.action,
            "reasoning": self.reasoning,
        }


@dataclass(frozen=True)
class HighPriorityIssueIdentified:
    """Event fired when a high priority issue is identified in a repository."""

    aggregate_id: str
    repo_name: str
    issue: Recommendation
    event_id: uuid.UUID = uuid.uuid4()
    timestamp: datetime = datetime.now(UTC)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation for serialization."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.__class__.__name__,
            "timestamp": self.timestamp.isoformat(),
            "aggregate_id": self.aggregate_id,
            "data": self._get_event_data(),
        }

    def _get_event_data(self) -> Dict[str, Any]:
        """Extract event-specific data for serialization."""
        return {
            "repo_name": self.repo_name,
            "recommendation": self.issue.recommendation,
            "reason": self.issue.reason,
            "priority": self.issue.priority,
        }


@dataclass(frozen=True)
class AnalysisError:
    """Event fired when an error occurs during repository analysis."""

    aggregate_id: str
    repo_name: str
    error_message: str
    event_id: uuid.UUID = uuid.uuid4()
    timestamp: datetime = datetime.now(UTC)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation for serialization."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.__class__.__name__,
            "timestamp": self.timestamp.isoformat(),
            "aggregate_id": self.aggregate_id,
            "data": self._get_event_data(),
        }

    def _get_event_data(self) -> Dict[str, Any]:
        """Extract event-specific data for serialization."""
        return {
            "repo_name": self.repo_name,
            "error": self.error_message,
        }
