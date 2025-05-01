"""Value objects for the Analysis bounded context.

These are immutable objects that represent domain concepts without identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RecommendedAction(Enum):
    """Possible actions that can be recommended for a repository."""

    DELETE = "DELETE"
    ARCHIVE = "ARCHIVE"
    EXTRACT = "EXTRACT"
    KEEP = "KEEP"
    PIN = "PIN"

    @classmethod
    def from_string(cls, value: str) -> RecommendedAction:
        """Convert a string to a RecommendedAction enum value."""
        try:
            return cls[value.upper()]
        except KeyError:
            return cls.KEEP  # Default to KEEP if invalid


class PriorityLevel(Enum):
    """Priority levels for recommendations."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @classmethod
    def from_string(cls, value: str) -> PriorityLevel:
        """Convert a string to a PriorityLevel enum value."""
        try:
            return cls[value.upper()]
        except KeyError:
            return cls.MEDIUM  # Default to MEDIUM if invalid


class ActivityLevel(Enum):
    """Activity level of a repository."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INACTIVE = "inactive"

    @classmethod
    def from_string(cls, value: str) -> ActivityLevel:
        """Convert a string assessment to an ActivityLevel enum value."""
        value_lower = value.lower()
        if "inactive" in value_lower or "none" in value_lower:
            return cls.INACTIVE
        if "high" in value_lower:
            return cls.HIGH
        if "low" in value_lower:
            return cls.LOW
        return cls.MEDIUM


class ValueLevel(Enum):
    """Value/importance level of a repository."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @classmethod
    def from_string(cls, value: str) -> ValueLevel:
        """Convert a string to a ValueLevel enum value."""
        try:
            return cls[value.upper()]
        except KeyError:
            return cls.MEDIUM  # Default to MEDIUM if invalid


@dataclass(frozen=True, slots=True)
class RepoAssessment:
    """Assessment of a repository's activity and value."""

    activity: ActivityLevel
    value: ValueLevel
    reasoning: str

    @classmethod
    def from_strings(
        cls,
        activity: str,
        value: str,
        reasoning: str,
    ) -> RepoAssessment:
        """Create a RepoAssessment from string values."""
        return cls(
            activity=ActivityLevel.from_string(activity),
            value=ValueLevel.from_string(value),
            reasoning=reasoning,
        )
