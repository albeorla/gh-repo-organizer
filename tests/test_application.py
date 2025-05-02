"""Unit tests for the *application* layer use-case analyse_repositories."""

from __future__ import annotations

from collections.abc import Sequence

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
        self.logger = None  # Add logger attribute

    # --- Port implementations --------------------------------------------

    def list_repositories(self, owner: str, *, limit: int | None = None):
        return self._repos[: limit or None]

    def fetch_languages(self, repo: Repository):
        return [LanguageBreakdown("Python", 100.0)]

    def recent_commits(self, repo: Repository, *, limit: int = 10):
        return []  # Return empty list instead of raising NotImplementedError

    def contributors(self, repo: Repository):
        return []  # Return empty list instead of raising NotImplementedError

    def get_repository_readme(self, repo_name: str):
        """Get a fake README for the repository."""
        return f"# {repo_name}\n\nThis is a test repository."


class _FakeAnalyzer:
    """Produces a trivial RepoAnalysis for every repository."""

    def analyze_repository(
        self, repo, readme_content=None, recent_commits=None, activity_summary=None
    ):
        return RepoAnalysis(
            repo_name=repo.name,
            summary=f"Analysis of {repo.name}",
            strengths=["Good documentation", "Active development"],
            weaknesses=["Limited test coverage", "Few contributors"],
            recommendations=[],
            activity_assessment="medium",
            estimated_value="medium",
            tags=["test", "python"],
            recommended_action="KEEP",
            action_reasoning="Test repository with good activity",
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
