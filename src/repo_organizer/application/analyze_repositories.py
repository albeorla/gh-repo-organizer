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
    single_repo: str | None = None,
) -> Sequence[RepoAnalysis]:
    """Return analyses for repositories owned by *owner*.

    Args:
        owner: GitHub user/org.
        source_control: Implementation of SourceControlPort.
        analyzer: Implementation of AnalyzerPort.
        limit: Optional maximum number of repos.
        single_repo: If specified, only analyze this specific repository.
    """
    # Get repos from source control
    repos: Sequence[Repository] = source_control.list_repositories(owner, limit=limit)
    
    # Filter for single repository if specified
    if single_repo:
        # Log the filter operation
        if hasattr(source_control, "logger") and source_control.logger:
            source_control.logger.log(f"Filtering repositories to only include: {single_repo}")
            
        filtered_repos = [repo for repo in repos if repo.name == single_repo]
        
        # Check if the specified repo was found
        if not filtered_repos:
            if hasattr(source_control, "logger") and source_control.logger:
                source_control.logger.log(
                    f"Repository '{single_repo}' not found in list of {len(repos)} repositories", 
                    level="error"
                )
                if repos:
                    source_control.logger.log(
                        f"Available repositories: {', '.join(repo.name for repo in repos[:10])}...", 
                        level="info"
                    )
            
            # Use empty list if repo not found
            return []
            
        repos = filtered_repos

    results: list[RepoAnalysis] = []
    for repo in repos:
        # Fetch languages (best-effort).  Not all adapters implement it yet.
        try:
            breakdown = source_control.fetch_languages(repo)
            languages_str = _breakdown_to_str(breakdown)
        except NotImplementedError:
            languages_str = "Unknown"

        # Fetch README content (best-effort)
        try:
            readme_content = source_control.get_repository_readme(repo.name)
            if not readme_content or readme_content.strip() == "":
                readme_content = "No README content available"
            
            # Log the README content for debugging
            if source_control.logger and getattr(source_control.logger, "debug_enabled", False):
                source_control.logger.log(
                    f"README content for {repo.name} (first 200 chars): {readme_content[:200]}...",
                    "debug",
                )
        except Exception as e:
            if source_control.logger:
                source_control.logger.log(f"Error fetching README: {str(e)}", "error")
            readme_content = "No README content available"
            
        # Get recent commits and activity info (best-effort)
        try:
            recent_commits = source_control.recent_commits(repo)
            recent_commits_count = len(recent_commits)
            activity_summary = f"{recent_commits_count} recent commits"
        except Exception:
            recent_commits_count = 0
            activity_summary = "No activity data available"
            
        repo_data: Mapping[str, object] = {
            "repo_name": repo.name,
            "repo_desc": repo.description or "No description",
            "repo_url": repo.url or "",
            "updated_at": repo.updated_at or "Unknown",
            "is_archived": repo.is_archived,
            "stars": repo.stars,
            "forks": repo.forks,
            "languages": languages_str,
            "readme_excerpt": readme_content,
            "recent_commits_count": recent_commits_count,
            "activity_summary": activity_summary,
            # Default values for other expected fields
            "open_issues": 0,
            "closed_issues": 0,
            "contributor_summary": "No contributor data available",
            "dependency_info": "No dependency information available",
            "dependency_context": ""
        }

        analysis = analyzer.analyze(repo_data)
        results.append(analysis)

    return results
