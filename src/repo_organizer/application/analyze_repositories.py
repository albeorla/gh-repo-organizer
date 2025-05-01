"""Use-case: analyse multiple GitHub repositories.

This module sits in the *application* layer - it wires together the
``SourceControlPort`` (to fetch metadata from GitHub) and the ``AnalyzerPort``
(to generate an in-depth analysis using an LLM or a rules-based engine).

The function is intentionally *stateless*; all dependencies are passed in as
arguments, which makes it trivial to test.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from repo_organizer.domain.analysis.models import RepoAnalysis
    from repo_organizer.domain.analysis.protocols import AnalyzerPort
    from repo_organizer.domain.source_control.protocols import (
        SourceControlPort,
    )


def _breakdown_to_str(breakdown) -> str:  # noqa: ANN001 - helper for formatting
    return ", ".join(f"{lb.language}: {lb.percentage:.1f}%" for lb in breakdown)


def _filter_single_repo(
    repos: Sequence[Any],  # type: ignore[type-arg]
    single_repo: str,
    source_control: SourceControlPort,  # type: ignore[valid-type]
) -> list[Any]:
    """Filter repositories to find a specific one.

    Args:
        repos: List of repositories
        single_repo: Name of the repository to find
        source_control: Source control port for logging

    Returns:
        List containing only the matching repository or empty list
    """
    matching_repos = [repo for repo in repos if repo.name == single_repo]
    if not matching_repos:
        if hasattr(source_control, "logger") and source_control.logger:
            msg = (
                f"Repository '{single_repo}' not found "
                f"in {len(repos)} repositories"
            )
            source_control.logger.log(msg, level="error")

            if repos:
                repo_list = ", ".join(repo.name for repo in repos[:10])
                source_control.logger.log(
                    f"Available repositories: {repo_list}...",
                    level="info",
                )
        return []
    return matching_repos


def _get_repo_readme(
    owner: str,
    repo_name: str,
    source_control: SourceControlPort,  # type: ignore[valid-type]
) -> str | None:
    """Fetch repository README content.

    Args:
        owner: Repository owner
        repo_name: Repository name
        source_control: Source control port

    Returns:
        README content or None if not available
    """
    try:
        readme_content = source_control.get_readme(owner, repo_name)
        if (
            hasattr(source_control, "logger")
            and source_control.logger
            and readme_content
        ):
            preview = readme_content[:200]
            source_control.logger.log(
                f"README content for {repo_name} (first 200 chars): {preview}...",
                "debug",
            )
    except OSError as e:
        if source_control.logger:
            source_control.logger.log(f"Error fetching README: {e!s}", "error")
        return None
    else:
        return readme_content


def _get_repo_activity(
    owner: str,
    repo_name: str,
    source_control: SourceControlPort,  # type: ignore[valid-type]
) -> tuple[int, str]:
    """Get repository activity information.

    Args:
        owner: Repository owner
        repo_name: Repository name
        source_control: Source control port

    Returns:
        Tuple of (commit count, activity summary)
    """
    try:
        recent_commits = source_control.get_recent_commits(owner, repo_name)
        recent_commits_count = len(recent_commits)
    except OSError as e:
        if source_control.logger:
            source_control.logger.log(f"Error fetching commits: {e!s}", "error")
        return 0, "No activity data available"
    else:
        return recent_commits_count, f"{recent_commits_count} recent commits"


def analyze_repositories(
    owner: str,
    source_control: SourceControlPort,  # type: ignore[valid-type]
    analyzer: AnalyzerPort,  # type: ignore[valid-type]
    single_repo: str | None = None,
    filters: Mapping | None = None,  # type: ignore[type-arg]
) -> Sequence[RepoAnalysis]:  # type: ignore[type-arg]
    """Analyze repositories for the given owner.

    Args:
        owner: GitHub username or organization
        source_control: Port for accessing GitHub API
        analyzer: Port for analyzing repositories
        single_repo: Optional single repository to analyze
        filters: Optional filters to apply

    Returns:
        List of repository analyses
    """
    repos = source_control.get_repositories(owner)

    if single_repo:
        repos = _filter_single_repo(repos, single_repo, source_control)
        if not repos:
            return []

    if filters:
        repos = [
            repo
            for repo in repos
            if all(
                getattr(repo, key, None) == value for key, value in filters.items()
            )
        ]

    analyses = []
    for repo in repos:
        readme_content = _get_repo_readme(owner, repo.name, source_control)
        commits_count, activity_summary = _get_repo_activity(
            owner,
            repo.name,
            source_control,
        )

        analysis = analyzer.analyze_repository(
            repo=repo,
            readme_content=readme_content,
            recent_commits=commits_count,
            activity_summary=activity_summary,
        )
        analyses.append(analysis)

    return analyses
