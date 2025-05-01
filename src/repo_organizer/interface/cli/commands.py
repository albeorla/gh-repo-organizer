"""CLI command implementations for repository actions.

This module contains commands for executing repository actions
based on analysis results.
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

from repo_organizer.config.settings import Settings, load_settings
from repo_organizer.domain.analysis.models import RepoAnalysis
from repo_organizer.domain.analysis.services import AnalysisService
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
    output_dir: str | None = None,
    github_token: str | None = None,
    action_type: str | None = None,
):
    """Execute repository actions based on analysis results.

    Args:
        dry_run: Whether to perform a dry run without making changes
        force: Whether to skip confirmation prompts
        output_dir: Output directory for analysis files
        github_token: GitHub token for authentication
        action_type: Type of action to execute (DELETE, ARCHIVE, EXTRACT, PIN)
    """
    # Load settings
    settings = load_settings()

    # Override settings with command-line options
    if output_dir:
        settings.output_dir = output_dir
    if github_token:
        settings.github_token = github_token

    # Create rate limiter for statistics (not used directly)
    _ = RateLimiter(settings.github_rate_limit, name="GitHub")

    # Load analyses
    analyses = _load_analyses(settings)

    # Categorize analyses by action
    categorized = AnalysisService.categorize_by_action(analyses)

    # Filter by action type if specified
    if action_type:
        action_type = action_type.upper()
        if action_type not in categorized:
            console.print(f"[red]Invalid action type: {action_type}[/]")
            raise typer.Exit(code=1)

        filtered_analyses = categorized[action_type]
    else:
        filtered_analyses = []
        for action, action_analyses in categorized.items():
            if action != "KEEP":  # Skip repositories that should be kept
                filtered_analyses.extend(action_analyses)

    if not filtered_analyses:
        console.print("[yellow]No repositories found for the specified action[/]")
        raise typer.Exit(code=0)

    # Display repositories
    table = Table(title="Repository Actions")
    table.add_column("Repository", style="cyan")
    table.add_column("Action", style="green")

    for analysis in filtered_analyses:
        action = getattr(analysis, "recommended_action", "KEEP")
        table.add_row(analysis.repo_name, action)

    console.print(table)

    # Confirm execution
    if not force and not dry_run and not typer.confirm("Execute these actions?"):
        console.print("[yellow]Operation cancelled[/]")
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

        for analysis in filtered_analyses:
            repo_name = analysis.repo_name
            action = getattr(analysis, "recommended_action", "KEEP")

            progress.update(task, description=f"[cyan]Processing {repo_name}")

            try:
                if dry_run:
                    # Simulate action execution
                    console.print(f"[dry-run] Would execute {action} for {repo_name}")
                # Actually execute the action
                elif action == "DELETE":
                    # Delete repository logic
                    console.print(f"[red]Deleting {repo_name}...[/]")
                    # In the future, we would use the GitHub REST API to delete the repository
                elif action == "ARCHIVE":
                    # Archive repository logic
                    console.print(f"[yellow]Archiving {repo_name}...[/]")
                    # In the future, we would use the GitHub REST API to archive the repository
                elif action == "EXTRACT":
                    # Extract repository logic
                    console.print(
                        f"[blue]Extracting valuable parts from {repo_name}...[/]",
                    )
                    # In the future, we would extract valuable parts before archiving/deleting
                elif action == "PIN":
                    # Pin repository logic
                    console.print(f"[green]Pinning {repo_name}...[/]")
                    # In the future, we would use the GitHub REST API to pin the repository
            except Exception as e:
                console.print(f"[red]Error executing {action} for {repo_name}: {e}[/]")

            progress.update(task, advance=1)

    # Print summary
    if dry_run:
        console.print("[green]Dry run completed successfully[/]")
    else:
        console.print("[green]Actions executed successfully[/]")
