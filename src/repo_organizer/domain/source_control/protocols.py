"""Ports (interfaces) for the *SourceControl* bounded context.

The application layer depends **only** on these Protocols – never on concrete
adapters – firmly following the Dependency Inversion Principle.
"""

from __future__ import annotations

from typing import Protocol, Sequence

from .models import Commit, Contributor, LanguageBreakdown, Repository


class SourceControlPort(Protocol):
    """Abstract interface for interacting with a source-control provider."""

    # ---------------------------------------------------------------------
    # Repository metadata
    # ---------------------------------------------------------------------

    def list_repositories(
        self, owner: str, *, limit: int | None = None
    ) -> Sequence[Repository]:
        """Return public repositories owned by *owner*.

        Args:
            owner: GitHub user/org name.
            limit: Maximum number of repos (``None`` for no limit).
        """

    # ---------------------------------------------------------------------
    # Repository details
    # ---------------------------------------------------------------------

    def fetch_languages(self, repo: Repository) -> Sequence[LanguageBreakdown]:
        """Return percentage breakdown of languages used in *repo*."""

    def recent_commits(self, repo: Repository, *, limit: int = 10) -> Sequence[Commit]:
        """Return the *latest* ``limit`` commits for *repo*."""

    def contributors(self, repo: Repository) -> Sequence[Contributor]:
        """Return contributors for *repo* sorted by commit count desc."""
