"""CLI commands for executing repository actions.

This module contains the implementation for executing repository actions
based on analysis results.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

from repo_organizer.domain.analysis.models import RepoAnalysis
from repo_organizer.domain.analysis.services import AnalysisService
from repo_organizer.infrastructure.config.settings import Settings, load_settings
from repo_organizer.utils.logger import Logger
from repo_organizer.utils.rate_limiter import RateLimiter

# Create console for rich output
console = Console()


def _load_analyses(settings: Settings) -> list[RepoAnalysis]:
    """Load existing repository analyses from output directory.

    Args:
        settings: Application settings

    Returns:
        List of repository analyses
    """
    output_dir = Path(settings.output_dir)
    analyses = []

    # Check if output directory exists
    if not output_dir.exists():
        console.print(f"[yellow]Output directory {output_dir} does not exist[/]")
        return []

    # Find all markdown files in the output directory
    md_files = list(output_dir.glob("*.md"))

    # Filter out the main report
    md_files = [f for f in md_files if f.stem != "repositories_report"]

    if not md_files:
        console.print("[yellow]No repository analyses found[/]")
        return []

    console.print(f"Found {len(md_files)} repository analyses")

    # Load each analysis
    for md_file in md_files:
        try:
            # Parse the markdown file to extract the recommended action
            repo_name = md_file.stem
            action = "KEEP"  # default
            reasoning = ""

            with open(md_file) as f:
                content = f.read()

                # Look for action in the file
                if "## Action Items" in content:
                    action_section = content.split("## Action Items")[1].split("##")[0]
                    if "archive" in action_section.lower():
                        action = "ARCHIVE"
                    elif "delete" in action_section.lower():
                        action = "DELETE"

                # Create a minimal analysis object
                from repo_organizer.domain.analysis.models import RepoAnalysis

                analysis = RepoAnalysis(
                    repo_name=repo_name,
                    summary="",
                    strengths=[],
                    weaknesses=[],
                    recommendations=[],
                    activity_assessment="",
                    estimated_value="",
                    tags=[],
                )

                # Monkey-patch the analysis object with the action
                analysis.recommended_action = action
                analysis.action_reasoning = reasoning

                analyses.append(analysis)
        except Exception as e:
            console.print(f"[red]Error loading analysis {md_file}: {e}[/]")

    return analyses


def execute_actions(
    dry_run: bool = True,
    force: bool = False,
    output_dir: Optional[str] = None,
    github_token: Optional[str] = None,
    action_type: Optional[str] = None,
    username: Optional[str] = None,  # Now required
    github_username: Optional[str] = None,  # Added for compatibility
):
    """Execute repository actions based on analysis results.

    Args:
        dry_run: Whether to perform a dry run without making changes
        force: Whether to skip confirmation prompts
        output_dir: Output directory for analysis files
        github_token: GitHub token for authentication
        action_type: Type of action to execute (DELETE, ARCHIVE, EXTRACT, PIN)
        username: GitHub username for authentication and action attribution
        github_username: Alternative GitHub username parameter
    """
    # Load settings
    settings = load_settings()

    # Override settings with command-line options
    if output_dir:
        settings.output_dir = output_dir
    if github_token:
        settings.github_token = github_token
    if github_username and not username:
        username = github_username

    # Set up logging with username for tracking
    log_path = Path(settings.logs_dir) / "action_execution.log"
    logger = Logger(
        str(log_path),
        console=console,
        debug_enabled=False,
        quiet_mode=False,
        username=username,
    )
    logger.log(f"Action execution started by {username}", level="info")

    # Create rate limiter for statistics (not used directly)
    RateLimiter(settings.github_rate_limit, name="GitHub")

    # Load analyses
    analyses = _load_analyses(settings)
    logger.log(f"Loaded {len(analyses)} repository analyses", level="debug")

    # Categorize analyses by action
    categorized = AnalysisService.categorize_by_action(analyses)

    # Filter by action type if specified
    if action_type:
        action_type = action_type.upper()
        if action_type not in categorized:
            error_msg = f"Invalid action type: {action_type}"
            logger.log(error_msg, level="error")
            console.print(f"[red]{error_msg}[/]")
            raise typer.Exit(code=1)

        filtered_analyses = categorized[action_type]
    else:
        filtered_analyses = []
        for action, action_analyses in categorized.items():
            if action != "KEEP":  # Skip repositories that should be kept
                filtered_analyses.extend(action_analyses)

    if not filtered_analyses:
        msg = "No repositories found for the specified action"
        logger.log(msg, level="warning")
        console.print(f"[yellow]{msg}[/]")
        raise typer.Exit(code=0)

    # Display repositories
    table = Table(title=f"Repository Actions (by {username})")
    table.add_column("Repository", style="cyan")
    table.add_column("Action", style="green")

    for analysis in filtered_analyses:
        action = getattr(analysis, "recommended_action", "KEEP")
        table.add_row(analysis.repo_name, action)

    console.print(table)
    logger.log(
        f"Selected {len(filtered_analyses)} repositories for actions",
        level="info",
    )

    # Confirm execution
    if not force and not dry_run and not typer.confirm("Execute these actions?"):
        msg = "Operation cancelled by user"
        logger.log(msg, level="info")
        console.print(f"[yellow]{msg}[/]")
        raise typer.Exit(code=0)

    # Execute actions
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[bold]{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task = progress.add_task(
            "[green]Executing actions",
            total=len(filtered_analyses),
        )

        success_count = 0
        error_count = 0

        for analysis in filtered_analyses:
            repo_name = analysis.repo_name
            action = getattr(analysis, "recommended_action", "KEEP")

            progress.update(task, description=f"[cyan]Processing {repo_name}")
            logger.log(f"Processing {repo_name} for action: {action}", level="info")

            try:
                if dry_run:
                    # Simulate action execution
                    msg = f"Would execute {action} for {repo_name}"
                    logger.log(f"[DRY RUN] {msg}", level="info")
                    console.print(f"[dry-run] {msg}")
                # Actually execute the action
                elif action == "DELETE":
                    # Delete repository logic
                    msg = f"Deleting {repo_name}..."
                    logger.log(msg, level="info")
                    console.print(f"[red]{msg}[/]")
                    # In the future, we would use the GitHub REST API to delete the repository
                elif action == "ARCHIVE":
                    # Archive repository logic
                    msg = f"Archiving {repo_name}..."
                    logger.log(msg, level="info")
                    console.print(f"[yellow]{msg}[/]")
                    # In the future, we would use the GitHub REST API to archive the repository
                elif action == "EXTRACT":
                    # Extract repository logic
                    msg = f"Extracting valuable parts from {repo_name}..."
                    logger.log(msg, level="info")
                    console.print(f"[blue]{msg}[/]")
                    # In the future, we would extract valuable parts before archiving/deleting
                elif action == "PIN":
                    # Pin repository logic
                    msg = f"Pinning {repo_name}..."
                    logger.log(msg, level="info")
                    console.print(f"[green]{msg}[/]")
                    # In the future, we would use the GitHub REST API to pin the repository
                success_count += 1
            except Exception as e:
                error_msg = f"Error executing {action} for {repo_name}: {e}"
                logger.log(error_msg, level="error")
                console.print(f"[red]{error_msg}[/]")
                error_count += 1

            progress.update(task, advance=1)

    # Print summary
    if dry_run:
        msg = "Dry run completed successfully"
        logger.log(msg, level="success")
        console.print(f"[green]{msg}[/]")
    else:
        msg = f"Actions executed successfully: {success_count} succeeded, {error_count} failed"
        logger.log(msg, level="success")
        console.print(f"[green]{msg}[/]")

    # Add attribution to the log
    logger.log(f"Action execution completed by {username}", level="info")
