"""Use-case: analyse multiple GitHub repositories.

This module sits in the *application* layer – it wires together the
``SourceControlPort`` (to fetch metadata from GitHub) and the ``AnalyzerPort``
(to generate an in-depth analysis using an LLM or a rules-based engine).

The function is intentionally *stateless*; all dependencies are passed in as
arguments, which makes it trivial to test.
"""

from __future__ import annotations

from typing import Mapping, Sequence

from repo_organizer.domain.analysis.models import RepoAnalysis
from repo_organizer.domain.analysis.protocols import AnalyzerPort
from repo_organizer.domain.source_control.models import Repository
from repo_organizer.domain.source_control.protocols import SourceControlPort


def _breakdown_to_str(breakdown) -> str:  # noqa: ANN001 – helper for formatting
    return ", ".join(f"{lb.language}: {lb.percentage:.1f}%" for lb in breakdown)


def analyze_repositories(
    owner: str,
    source_control: SourceControlPort,
    analyzer: AnalyzerPort,
    *,
    limit: int | None = None,
) -> Sequence[RepoAnalysis]:
    """Return analyses for repositories owned by *owner*.

    Args:
        owner: GitHub user/org.
        source_control: Implementation of SourceControlPort.
        analyzer: Implementation of AnalyzerPort.
        limit: Optional maximum number of repos.
    """

    repos: Sequence[Repository] = source_control.list_repositories(owner, limit=limit)

    results: list[RepoAnalysis] = []
    for repo in repos:
        # Fetch languages (best-effort).  Not all adapters implement it yet.
        try:
            breakdown = source_control.fetch_languages(repo)
            languages_str = _breakdown_to_str(breakdown)
        except NotImplementedError:
            languages_str = "Unknown"

        repo_data: Mapping[str, object] = {
            "repo_name": repo.name,
            "repo_desc": repo.description or "No description",
            "repo_url": repo.url or "",
            "updated_at": repo.updated_at or "Unknown",
            "is_archived": repo.is_archived,
            "stars": repo.stars,
            "forks": repo.forks,
            "languages": languages_str,
        }

        analysis = analyzer.analyze(repo_data)
        results.append(analysis)

    return results
