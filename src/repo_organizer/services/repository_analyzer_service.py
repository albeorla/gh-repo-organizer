"""Repository analyzer service implementation.

This module contains the main repository analysis logic, following the SOLID principles
with a clear separation of concerns.
"""

import os
import re
from typing import Any

from repo_organizer.domain.analysis.protocols import AnalyzerPort
from repo_organizer.infrastructure.analysis.pydantic_models import RepoAnalysis
from repo_organizer.infrastructure.source_control.github_service import GitHubService
from repo_organizer.utils.logger import Logger


class RepositoryAnalyzerService:
    """Orchestrates the repository analysis process.

    This service follows the Single Responsibility Principle by focusing solely
    on coordinating the repository analysis workflow.
    """

    def __init__(
        self,
        output_dir: str = ".out",
        api_key: str | None = None,
        github_service: GitHubService | None = None,
        analyzer: AnalyzerPort | None = None,
        max_repos: int | None = None,
        debug: bool = False,
        repo_filter: str | None = None,
        force_reanalyze: bool = False,
        *,
        logger: Logger | None = None,
    ):
        """Initialize the repository analyzer service.

        Args:
            output_dir: The directory to store output in.
            api_key: The Claude API key.
            github_service: The GitHub service instance.
            analyzer: The analyzer implementing AnalyzerPort.
            max_repos: The maximum number of repos to analyze.
            debug: Whether to enable debug logging.
            repo_filter: A regex filter for repo names.
            force_reanalyze: Whether to force reanalysis of repos even if report exists.
        """
        self.output_dir = output_dir
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.github_service = github_service
        self.analyzer = analyzer
        self.max_repos = max_repos
        self.repo_filter = repo_filter
        self.force_reanalyze = force_reanalyze

        # ------------------------------------------------------------------
        # Logging
        # ------------------------------------------------------------------
        # Re-use the shared application-level logger when one is supplied.  This
        # prevents interleaved messages from multiple Logger instances and
        # ensures all output is consolidated in the same log file.  Fallback to
        # creating a private logger when running the service standalone (e.g.
        # during unit tests).
        if logger is not None:
            self.logger = logger
        else:
            # Keep the legacy behaviour: write a single analysis.log file next
            # to the output directory.  Ensure its parent directory exists.
            logs_path = os.path.join(os.path.dirname(self.output_dir), "analysis.log")
            os.makedirs(os.path.dirname(logs_path), exist_ok=True)
            self.logger = Logger(logs_path, debug_enabled=debug)

        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)

    def _should_analyze_repo(self, repo_name: str) -> bool:
        """Determine if a repository should be analyzed.

        Args:
            repo_name: The name of the repository.

        Returns:
            bool: Whether the repository should be analyzed.
        """
        report_path = os.path.join(self.output_dir, f"{repo_name}.md")

        # Skip if report already exists and we're not forcing reanalysis
        if os.path.exists(report_path) and not self.force_reanalyze:
            self.logger.log(
                f"Skipping {repo_name} - report already exists", level="info",
            )
            return False

        # If a filter is provided, check if the repo matches
        if self.repo_filter:
            pattern = re.compile(self.repo_filter)
            if not pattern.search(repo_name):
                self.logger.log(
                    f"Skipping {repo_name} - doesn't match filter '{self.repo_filter}'",
                    level="debug",
                )
                return False

        return True

    def analyze_repository(self, repo_info: dict[str, Any]) -> RepoAnalysis:
        """Analyze a single repository.

        Args:
            repo_info: Repository information dictionary

        Returns:
            Repository analysis object
        """
        # Handle both ``name`` (REST/Git) and ``repo_name`` (internal prompt
        # preparation or unit-test fixtures).
        repo_name = repo_info.get("name") or repo_info.get("repo_name", "unknown")
        if not self._should_analyze_repo(repo_name):
            self.logger.log(f"Skipping analysis for {repo_name}", level="info")
            self.logger.update_stats("repos_skipped")

            # Create a placeholder analysis with skipped tag
            return RepoAnalysis(
                repo_name=repo_name,
                summary="Repository analysis was skipped",
                strengths=["Analysis skipped"],
                weaknesses=["Analysis skipped"],
                recommendations=[],
                activity_assessment="Unknown (analysis skipped)",
                estimated_value="Unknown (analysis skipped)",
                tags=["skipped"],
            )

        try:
            self.logger.log(f"Analyzing repository: {repo_name}", level="info")

            # Prepare input data for LLM
            analysis_input = self._prepare_repo_data(repo_info)

            # Use analyzer (implements AnalyzerPort) to analyze the repository
            if self.analyzer:
                # Convert to domain model
                domain_analysis = self.analyzer.analyze(analysis_input)

                # Convert back to Pydantic model for backward compatibility
                analysis = domain_analysis.to_pydantic()

                # Ensure the repository name in the analysis matches the real repository name.
                # The LLM occasionally "corrects" or reformats the name, which causes issues
                # with filename consistency
                analysis.repo_name = repo_name

                self.logger.log(f"Successfully analyzed {repo_name}", level="success")
                self.logger.update_stats("repos_analyzed")

                return analysis
            self.logger.log(
                f"Analyzer not available for {repo_name}", level="error",
            )
            self.logger.update_stats("repos_failed")

            # Create a placeholder analysis with error tag
            return RepoAnalysis(
                repo_name=repo_name,
                summary="Analyzer not available",
                strengths=["Analysis failed"],
                weaknesses=["Analysis failed"],
                recommendations=[],
                activity_assessment="Unknown (analysis failed)",
                estimated_value="Unknown (analysis failed)",
                tags=["error", "service-unavailable"],
            )
        except Exception as e:
            self.logger.log(f"Error analyzing {repo_name}: {e!s}", level="error")
            self.logger.update_stats("repos_failed")

            # Create a placeholder analysis with error tag
            return RepoAnalysis(
                repo_name=repo_name,
                summary=f"Error analyzing repository: {e!s}",
                strengths=["Analysis failed"],
                weaknesses=["Analysis failed"],
                recommendations=[],
                activity_assessment="Unknown (analysis failed)",
                estimated_value="Unknown (analysis failed)",
                tags=["error", "analysis-failed"],
            )

    def _prepare_repo_data(self, repo_info: dict[str, Any]) -> dict[str, Any]:
        """Prepare repository data for LLM analysis.

        Args:
            repo_info: Repository information from GitHub API

        Returns:
            Dictionary with all data needed for LLM analysis
        """
        repo_name = repo_info.get("name") or repo_info.get("repo_name", "unknown")

        # Get language breakdown if GitHub service is available
        languages_str = "Unknown"
        if self.github_service:
            languages_data = self.github_service.get_repo_languages(repo_name)
            if languages_data:
                languages_str = ", ".join(
                    [f"{lang}: {pct:.1f}%" for lang, pct in languages_data.items()],
                )

        # Get additional repository data for more accurate analysis
        issues_data = {"open_count": 0, "closed_count": 0, "recent_activity": False}
        commit_data = {
            "recent_commits": 0,
            "active_last_month": False,
            "active_last_year": False,
        }
        contributor_data = {"count": 0, "active_contributors": 0}
        dependency_data = {"has_dependency_files": False, "dependency_files": []}

        if self.github_service:
            # Gather enhanced data about the repository
            issues_data = self.github_service.get_repo_issues_stats(repo_name)
            commit_data = self.github_service.get_repo_commit_activity(repo_name)
            contributor_data = self.github_service.get_repo_contributors_stats(
                repo_name,
            )
            dependency_data = self.github_service.get_repo_dependency_files(repo_name)

        # Don't use local repositories for analysis to avoid confusion
        # We'll focus on the API data instead
        recent_commits_str = "Data not available via API"
        contributor_list_str = "Data not available via API"

        # Prepare input for LLM
        # GitHub's REST and GraphQL APIs use different field names for similar
        # attributes (e.g. ``updated_at`` vs ``updatedAt``).  The service was
        # originally built against GraphQL but was later migrated to the REST
        # endpoints for simplicity.  To remain backward-compatible – and more
        # importantly to *always* populate the prompt with correct values – we
        # transparently fall back to the REST field names when the GraphQL
        # ones are missing.

        updated_at = (
            repo_info.get("updatedAt")  # GraphQL name
            or repo_info.get("updated_at")  # REST name
            or "Unknown"
        )
        # Simplify timestamp to *date* only (YYYY-MM-DD) when possible.
        if isinstance(updated_at, str) and "T" in updated_at:
            updated_at = updated_at.split("T")[0]

        stars = (
            repo_info.get("stargazerCount")
            or repo_info.get("stargazers_count")
            or repo_info.get("stars", 0)
        )
        forks = (
            repo_info.get("forkCount")
            or repo_info.get("forks_count")
            or repo_info.get("forks", 0)
        )

        is_archived = repo_info.get("isArchived")
        if is_archived is None:  # REST uses ``archived`` (bool)
            is_archived = repo_info.get("archived", False)

        repo_url = (
            repo_info.get("url")
            or repo_info.get("html_url")
            or repo_info.get("repo_url", "")
        )

        # Format activity data
        activity_summary = "No recent activity detected"
        if commit_data["active_last_month"]:
            activity_summary = "Very active (commits within the last month)"
        elif commit_data["active_last_year"]:
            activity_summary = "Somewhat active (commits within the last year)"
        else:
            activity_summary = "Inactive (no commits within the last year)"

        # Add issue activity
        if issues_data["recent_activity"]:
            activity_summary += ", recent issue activity"

        # Format contributor data
        contributor_summary = f"{contributor_data['count']} contributors"
        if contributor_data["count"] > 0:
            contributor_summary += (
                f" ({contributor_data['active_contributors']} active)"
            )

        # Format dependency information
        dependency_summary = "No dependency files detected"
        if dependency_data["has_dependency_files"]:
            dependency_summary = (
                f"Dependency files: {', '.join(dependency_data['dependency_files'])}"
            )

        # Format content samples if available (for context)
        dependency_context = ""
        if dependency_data.get("content_samples"):
            # Only include one sample to avoid making the prompt too long
            for file_name, content in dependency_data["content_samples"].items():
                dependency_context = f"Sample from {file_name}:\n{content[:300]}..."
                break  # Just take the first one

        return {
            "repo_name": repo_name,
            "repo_desc": repo_info.get("description", "No description available"),
            "repo_url": repo_url,
            "updated_at": updated_at,
            "is_archived": is_archived,
            "stars": stars,
            "forks": forks,
            "languages": languages_str,
            "has_local": False,  # Always set to false to avoid local repo confusion
            "recent_commits": recent_commits_str,
            "contributor_list": contributor_list_str,
            # Enhanced data for better analysis
            "open_issues": issues_data["open_count"],
            "closed_issues": issues_data["closed_count"],
            "activity_summary": activity_summary,
            "recent_commits_count": commit_data["recent_commits"],
            "contributor_summary": contributor_summary,
            "dependency_info": dependency_summary,
            "dependency_context": dependency_context,
            # Include a truncated README excerpt to provide additional context
            "readme_excerpt": self.github_service.get_repo_readme(repo_name)
            if self.github_service
            else "",
        }

    def _write_single_report(
        self, analysis: RepoAnalysis, repo_info: dict[str, Any],
    ) -> None:
        """Write the markdown report for a single repository.

        Args:
            analysis: Repository analysis result
            repo_info: Repository information dictionary
        """
        repo_name = analysis.repo_name
        repo_file_path = os.path.join(self.output_dir, f"{repo_name}.md")
        self.logger.log(
            f"Saving report for {repo_name} to {repo_file_path}...", level="debug",
        )

        try:
            with open(repo_file_path, "w") as f:
                f.write(f"# {repo_name}\n\n")

                f.write("## Basic Information\n\n")
                # Prefer the human-facing ``html_url`` when available.  Fall
                # back to ``url`` (the REST API endpoint) to avoid breaking in
                # edge-cases where the field might be missing (e.g. during
                # unit-tests with stubbed data).
                repo_link = repo_info.get("html_url") or repo_info.get("url", "")
                f.write(f"- **URL**: [{repo_link}]({repo_link})\n")
                f.write(
                    f"- **Description**: {repo_info.get('description', 'No description')}\n",
                )
                # Handle both GraphQL and REST field names (see above)
                updated_at = repo_info.get("updatedAt") or repo_info.get(
                    "updated_at", "Unknown",
                )
                if isinstance(updated_at, str) and "T" in updated_at:
                    updated_at = updated_at.split("T")[0]

                is_archived = repo_info.get("isArchived")
                if is_archived is None:
                    is_archived = repo_info.get("archived", False)

                stars = repo_info.get("stargazerCount") or repo_info.get(
                    "stargazers_count", 0,
                )
                forks = repo_info.get("forkCount") or repo_info.get("forks_count", 0)

                f.write(f"- **Last Updated**: {updated_at}\n")
                f.write(f"- **Archived**: {is_archived}\n")
                f.write(f"- **Stars**: {stars}\n")
                f.write(f"- **Forks**: {forks}\n\n")

                f.write("## Analysis Summary\n\n")
                # Process string fields to ensure newlines are properly formatted
                summary = (
                    analysis.summary.replace("\\n", "\n") if analysis.summary else ""
                )
                f.write(f"{summary}\n\n")

                f.write("### Strengths\n\n")
                for strength in analysis.strengths:
                    strength_text = strength.replace("\\n", "\n") if strength else ""
                    f.write(f"- {strength_text}\n")
                f.write("\n")

                f.write("### Areas for Improvement\n\n")
                for weakness in analysis.weaknesses:
                    weakness_text = weakness.replace("\\n", "\n") if weakness else ""
                    f.write(f"- {weakness_text}\n")
                f.write("\n")

                f.write("### Recommendations\n\n")
                for rec in analysis.recommendations:
                    recommendation = (
                        rec.recommendation.replace("\\n", "\n")
                        if rec.recommendation
                        else ""
                    )
                    reason = rec.reason.replace("\\n", "\n") if rec.reason else ""
                    f.write(f"- **{recommendation}** ({rec.priority} Priority)  \n")
                    f.write(f"  *Reason: {reason}*\n")
                f.write("\n")

                f.write("### Assessment\n\n")
                activity = (
                    analysis.activity_assessment.replace("\\n", "\n")
                    if analysis.activity_assessment
                    else ""
                )
                value = (
                    analysis.estimated_value.replace("\\n", "\n")
                    if analysis.estimated_value
                    else ""
                )
                f.write(f"- **Activity Level**: {activity}\n")
                f.write(f"- **Estimated Value**: {value}\n")

                # Process tags to ensure no escaped newlines
                tags = [
                    tag.replace("\\n", "\n") if tag else "" for tag in analysis.tags
                ]
                f.write(f"- **Tags**: {', '.join(tags)}\n\n")

                f.write("## Action Items\n\n")
                f.write("- [ ] Review repository and confirm assessed value\n")
                f.write("- [ ] Implement high-priority recommendations\n")
                f.write("- [ ] Update documentation if keeping\n")
                if value.lower().startswith("low") or "low" in value.lower():
                    f.write(
                        "- [ ] Consider archiving or deleting if no longer needed\n",
                    )

            self.logger.log(
                f"Successfully saved report for {repo_name}", level="success",
            )
        except Exception as e:
            self.logger.log(
                f"ERROR saving report for {repo_name} at {repo_file_path}: {e}",
                level="error",
            )
            if hasattr(self.logger, "debug_enabled") and self.logger.debug_enabled:
                import traceback

                self.logger.log(
                    f"Traceback (saving {repo_name} report):\n{traceback.format_exc()}",
                    level="debug",
                )

    def generate_report(
        self, repos: list[dict[str, Any]], analyses: list[RepoAnalysis],
    ) -> None:
        """Generate a summary report of all repository analyses.

        Args:
            repos: List of repository information dictionaries
            analyses: List of repository analysis results
        """
        report_path = os.path.join(self.output_dir, "repositories_report.md")
        self.logger.log(f"Generating summary report at {report_path}...", level="info")

        try:
            with open(report_path, "w") as f:
                f.write("# GitHub Repositories Summary Report\n\n")
                import datetime

                f.write(
                    f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d')}\n\n",
                )

                # Group repositories by value
                high_value = [
                    a for a in analyses if "high" in a.estimated_value.lower()
                ]
                medium_value = [
                    a for a in analyses if "medium" in a.estimated_value.lower()
                ]
                low_value = [a for a in analyses if "low" in a.estimated_value.lower()]
                other_value = [
                    a
                    for a in analyses
                    if not any(
                        x in a.estimated_value.lower()
                        for x in ["high", "medium", "low"]
                    )
                ]

                # Write high-value repositories
                f.write("## High-Value Repositories\n\n")
                if high_value:
                    for analysis in high_value:
                        f.write(
                            f"### [{analysis.repo_name}]({analysis.repo_name}.md)\n\n",
                        )
                        f.write(f"{analysis.summary}\n\n")
                        f.write(f"**Tags**: {', '.join(analysis.tags)}\n\n")
                else:
                    f.write("No high-value repositories found.\n\n")

                # Write medium-value repositories
                f.write("## Medium-Value Repositories\n\n")
                if medium_value:
                    for analysis in medium_value:
                        f.write(
                            f"### [{analysis.repo_name}]({analysis.repo_name}.md)\n\n",
                        )
                        f.write(f"{analysis.summary}\n\n")
                        f.write(f"**Tags**: {', '.join(analysis.tags)}\n\n")
                else:
                    f.write("No medium-value repositories found.\n\n")

                # Write low-value repositories
                f.write("## Low-Value Repositories\n\n")
                if low_value:
                    for analysis in low_value:
                        f.write(
                            f"### [{analysis.repo_name}]({analysis.repo_name}.md)\n\n",
                        )
                        f.write(f"{analysis.summary}\n\n")
                        f.write(f"**Tags**: {', '.join(analysis.tags)}\n\n")
                else:
                    f.write("No low-value repositories found.\n\n")

                # Write other repositories
                if other_value:
                    f.write("## Other Repositories\n\n")
                    for analysis in other_value:
                        f.write(
                            f"### [{analysis.repo_name}]({analysis.repo_name}.md)\n\n",
                        )
                        f.write(f"{analysis.summary}\n\n")
                        f.write(f"**Tags**: {', '.join(analysis.tags)}\n\n")

                # Write statistics
                f.write("## Repository Statistics\n\n")
                f.write(f"- Total repositories analyzed: {len(analyses)}\n")
                f.write(f"- High-value repositories: {len(high_value)}\n")
                f.write(f"- Medium-value repositories: {len(medium_value)}\n")
                f.write(f"- Low-value repositories: {len(low_value)}\n")
                f.write(f"- Other repositories: {len(other_value)}\n")

            self.logger.log(
                f"Successfully generated summary report at {report_path}",
                level="success",
            )
        except Exception as e:
            self.logger.log(f"ERROR generating summary report: {e}", level="error")
            if hasattr(self.logger, "debug_enabled") and self.logger.debug_enabled:
                import traceback

                self.logger.log(
                    f"Traceback (generating summary report):\n{traceback.format_exc()}",
                    level="debug",
                )
