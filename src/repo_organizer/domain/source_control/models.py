"""Domain model for the *SourceControl* bounded context.

The classes defined here are **pure** data structures (value objects /
aggregates).  They **must not** import from infrastructure-level packages to
stay independent of external libraries.  Where possible we use
``@dataclass(frozen=True)`` because immutability simplifies reasoning and
helps maintain referential transparency.

For the initial refactor sprint we simply *delegate* to the already existing
Pydantic models under ``repo_organizer.models.repo_models`` to avoid code
duplication.  In a later stage we may gradually migrate towards lightweight
``dataclasses``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


###############################################################################
# Value Objects
###############################################################################


@dataclass(frozen=True, slots=True)
class LanguageBreakdown:
    """Percentage of code written in a given programming language."""

    language: str
    percentage: float  # 0-100 inclusive

    def __post_init__(self) -> None:  # noqa: D401
        if not (0.0 <= self.percentage <= 100.0):
            raise ValueError("percentage must be between 0 and 100")


###############################################################################
# Aggregate Roots
###############################################################################


@dataclass(frozen=True, slots=True)
class Commit:
    """A single Git commit."""

    hash: str
    message: str
    author: str
    date: str  # ISO-8601 string – keeps it simple for now


@dataclass(frozen=True, slots=True)
class Contributor:
    """Repository contributor + number of commits."""

    name: str
    commits: int


@dataclass(frozen=True, slots=True)
class Repository:
    """Aggregate root representing a Git repository on a remote host."""

    name: str
    description: str | None
    url: str | None
    updated_at: str | None  # ISO string from GitHub – no datetime for now
    is_archived: bool
    stars: int
    forks: int
    languages: Sequence[LanguageBreakdown] | None = None

    # Convenience helpers -----------------------------------------------------
    def with_languages(self, breakdown: Mapping[str, float]) -> "Repository":
        """Return a *new* instance containing language percentages."""

        lb = [LanguageBreakdown(lang, pct) for lang, pct in breakdown.items()]
        return Repository(
            name=self.name,
            description=self.description,
            url=self.url,
            updated_at=self.updated_at,
            is_archived=self.is_archived,
            stars=self.stars,
            forks=self.forks,
            languages=lb,
        )
