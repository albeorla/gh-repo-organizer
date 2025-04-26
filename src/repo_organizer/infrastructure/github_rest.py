"""GitHub REST adapter implementing the ``SourceControlPort``.

The class composes (for now *inherits*) the existing ``GitHubService`` to avoid
duplicating logic while the refactor is in progress.  Once all call sites have
migrated to the new port we can clean up the inheritance relationship and use
*pure* composition.
"""

from __future__ import annotations

from typing import Sequence

from repo_organizer.domain.source_control.models import (
    Commit,
    Contributor,
    LanguageBreakdown,
    Repository,
)
from repo_organizer.domain.source_control.protocols import SourceControlPort
from repo_organizer.services.github_service import GitHubService


class GitHubRestAdapter(GitHubService, SourceControlPort):
    """Adapter that fulfils ``SourceControlPort`` using the GitHub REST API."""

    # ------------------------------------------------------------------
    # SourceControlPort implementation
    # ------------------------------------------------------------------

    def list_repositories(
        self, owner: str, *, limit: int | None = None
    ) -> Sequence[Repository]:
        # ``GitHubService`` is initialised with a username already -> validate
        if owner != self.github_username:
            raise ValueError(
                "GitHubRestAdapter currently only supports the owner passed at construction time"
            )

        raw_repos = super().get_repos(limit=limit or 1000)

        repos: list[Repository] = []
        for r in raw_repos:
            repos.append(
                Repository(
                    name=r["name"],
                    description=r.get("description"),
                    url=r.get("url"),
                    updated_at=r.get("updatedAt"),
                    is_archived=r.get("isArchived", False),
                    stars=r.get("stargazerCount", 0),
                    forks=r.get("forkCount", 0),
                )
            )
            if limit and len(repos) >= limit:
                break

        return repos

    def fetch_languages(self, repo: Repository) -> Sequence[LanguageBreakdown]:
        breakdown = super().get_repo_languages(repo.name)
        return [LanguageBreakdown(lang, pct) for lang, pct in breakdown.items()]

    def recent_commits(self, repo: Repository, *, limit: int = 10) -> Sequence[Commit]:
        # Reuse existing implementation that operates on local path
        # NOTE: For remote-only mode we would need extra API calls – out of scope
        # for the MVP.  We therefore raise *NotImplementedError* to be explicit.
        raise NotImplementedError(
            "Fetching commits not yet implemented in REST adapter"
        )

    def contributors(self, repo: Repository) -> Sequence[Contributor]:
        raise NotImplementedError(
            "Fetching contributors not yet implemented in REST adapter"
        )
