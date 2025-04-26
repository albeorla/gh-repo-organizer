"""Unit tests for the *application* layer use-case analyse_repositories."""

from __future__ import annotations

from typing import Sequence

import pytest

from repo_organizer.application import analyze_repositories
from repo_organizer.domain.analysis.models import RepoAnalysis
from repo_organizer.domain.source_control.models import (
    LanguageBreakdown,
    Repository,
)


# ---------------------------------------------------------------------------
# In-memory fakes for ports – no external I/O.
# ---------------------------------------------------------------------------


class _FakeSourceControl:
    """Returns a static list of repositories and synthetic language stats."""

    def __init__(self, repos: Sequence[Repository]):
        self._repos = list(repos)

    # --- Port implementations --------------------------------------------

    def list_repositories(self, owner: str, *, limit: int | None = None):  # noqa: D401
        return self._repos[: limit or None]

    def fetch_languages(self, repo: Repository):  # noqa: D401
        return [LanguageBreakdown("Python", 100.0)]

    def recent_commits(self, repo: Repository, *, limit: int = 10):  # noqa: D401
        raise NotImplementedError

    def contributors(self, repo: Repository):  # noqa: D401
        raise NotImplementedError


class _FakeAnalyzer:
    """Produces a trivial RepoAnalysis for every repository."""

    def analyze(self, repo_data):  # noqa: D401 ANN001
        return RepoAnalysis(
            repo_name=repo_data["repo_name"],
            summary="dummy",
            strengths=["s"],
            weaknesses=["w"],
            recommendations=[],
            activity_assessment="low",
            estimated_value="low",
            tags=["t"],
        )


def test_analyze_repositories():
    repos = [
        Repository(
            name="repo1",
            description="d",
            url="u",
            updated_at="2025-04-26",
            is_archived=False,
            stars=1,
            forks=0,
        ),
        Repository(
            name="repo2",
            description="d2",
            url="u2",
            updated_at="2025-04-25",
            is_archived=False,
            stars=2,
            forks=1,
        ),
    ]

    sc = _FakeSourceControl(repos)
    analyzer = _FakeAnalyzer()

    results = analyze_repositories("owner", sc, analyzer)

    assert isinstance(results, Sequence)
    assert len(results) == 2
    assert all(isinstance(r, RepoAnalysis) for r in results)
    assert {r.repo_name for r in results} == {"repo1", "repo2"}
