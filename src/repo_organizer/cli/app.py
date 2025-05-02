"""Command-line interface for the GitHub Repository Organizer.

This module provides a modern CLI using Typer with rich integration for
an enhanced user experience.
"""

import os
import time
from enum import Enum
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.syntax import Syntax
from rich.table import Table

from repo_organizer.cli.auth_middleware import authenticate_command
from repo_organizer.cli.commands import execute_actions

# Import needed for running the CLI without accessing it through the entry points
# This prevents relative import errors when running the CLI directly
from repo_organizer.infrastructure.config.settings import load_settings

from .dev import dev_app


# Define Enum for action types
class ActionType(str, Enum):
    """Repository action types."""

    DELETE = "delete"
    ARCHIVE = "archive"
    EXTRACT = "extract"
    KEEP = "keep"
    PIN = "pin"
    ALL = "all"


# Create Typer app with rich integration
app = typer.Typer(
    name="repo-analyzer",
    help="Analyze GitHub repositories and provide insights using AI.",
    add_completion=True,
)

# Temporarily disable authentication option for testing
# with_auth_option(app)

# Create console for rich output
console = Console()


def version_callback(value: bool):
    """Display version information and exit."""
    if value:
        from repo_organizer import __version__

        console.print(
            f"[bold green]GitHub Repository Analyzer[/] version: [bold]{__version__}[/]",
        )
        typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
):
    """Analyze GitHub repositories using LangChain and Anthropic's Claude AI.

    This tool provides insights, recommendations, and documentation for repositories that you own (not repositories you've starred or forked).
    """


@app.command()
# Temporarily disable authentication for testing
# @authenticate_command("analyze")
def analyze(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force re-analysis of all repositories, ignoring cached results.",
    ),
    output_dir: str = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Directory to output analysis results (default: .out/repos).",
    ),
    limit: int = typer.Option(
        None,
        "--limit",
        "-l",
        help="Maximum number of repositories to analyze.",
    ),
    max_repos: int | None = typer.Option(
        None,
        "--max-repos",
        "-m",
        help="Maximum number of repositories to analyze (deprecated, use --limit).",
    ),
    owner: str = typer.Option(None, "--owner", help="GitHub owner/user to analyze."),
    single_repo: str | None = typer.Option(
        None,
        "--single-repo",
        "-s",
        help="Process only a single repository by name.",
    ),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug logging."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimize console output."),
    username: str | None = None,  # Added by with_auth_option, manually included here for clarity
):
    """Analyze GitHub repositories and generate detailed reports.

    This command uses Domain-Driven Design (DDD) architecture to provide accurate
    repository analysis with proper separation of concerns, improved error handling,
    and better maintainability.
    """
    # For backwards compatibility
    if max_repos is not None and limit is None:
        limit = max_repos

    # Use the DDD approach
    from pathlib import Path

    from repo_organizer.application.analyze_repositories import analyze_repositories
    from repo_organizer.infrastructure.config.settings import load_settings
    from repo_organizer.infrastructure.analysis.langchain_claude_adapter import (
        LangChainClaudeAdapter,
    )

    # Import directly from bounded context modules to avoid circular imports
    from repo_organizer.infrastructure.github_rest import GitHubRestAdapter
    from repo_organizer.utils.logger import Logger
    from repo_organizer.utils.rate_limiter import RateLimiter

    settings = load_settings()

    # Apply single repository option to settings if provided via command line
    if single_repo:
        settings.single_repo = single_repo
        if not quiet:
            console.print(
                f"[cyan]Single repository mode: Will only process [bold]{single_repo}[/][/]",
            )

    # Resolve owner
    if owner is None:
        if settings.github_username:
            owner = settings.github_username
        else:
            console.print(
                "[red]Owner not specified and GITHUB_USERNAME missing in env[/]",
            )
            raise typer.Exit(1)

    # Resolve output directory
    if output_dir is None:
        output_path = Path(settings.output_dir)
    else:
        import os

        expanded_output = os.path.abspath(
            os.path.expanduser(os.path.expandvars(output_dir)),
        )
        output_path = Path(expanded_output)

    if not quiet:
        console.print("")  # Add a blank line for better output formatting

    with console.status(
        "[bold green]Starting repository analysis...[/]",
        spinner="dots",
    ):
        # Create the output directory
        output_path.mkdir(parents=True, exist_ok=True)

        # Setup logger
        log_path = output_path / "analysis.log"
        logger = Logger(str(log_path), console, debug_enabled=debug, quiet_mode=quiet)

        # Setup rate limiters
        github_lim = RateLimiter(settings.github_rate_limit, name="GitHub")
        llm_lim = RateLimiter(settings.llm_rate_limit, name="LLM")

        # Create adapters using DDD approach
        github = GitHubRestAdapter(
            github_username=owner,
            github_token=settings.github_token,
            rate_limiter=github_lim,
            logger=logger,
        )

        llm = LangChainClaudeAdapter(
            api_key=settings.anthropic_api_key,
            model_name=settings.llm_model,
            temperature=settings.llm_temperature,
            thinking_enabled=settings.llm_thinking_enabled,
            thinking_budget=settings.llm_thinking_budget,
            rate_limiter=llm_lim,
            logger=logger,
        )

    # Start the repository analysis
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
        TextColumn("[bold]{task.fields[status]}"),
        TextColumn("[dim]{task.fields[details]}"),
        console=console,
        expand=True,
        transient=False,
        refresh_per_second=5,
        get_time=None,
    ) as progress:
        fetch_task = progress.add_task(
            "[cyan]Fetching repositories",
            total=1,
            status="Starting...",
            details="",
        )

        try:
            if not quiet:
                if settings.single_repo:
                    console.print(
                        f"[cyan]Fetching repository [bold]{settings.single_repo}[/] for [bold]{owner}[/]...",
                    )
                else:
                    console.print(
                        f"[cyan]Fetching repositories for [bold]{owner}[/]...",
                    )

            analyses = analyze_repositories(
                owner,
                github,
                llm,
                limit=limit,
                single_repo=settings.single_repo,
            )
            progress.update(
                fetch_task,
                completed=1,
                status="Done",
                details=f"Found {len(analyses)} repositories",
            )

            # Create a new task for analyzing repositories
            task = progress.add_task(
                "[green]Analyzing repositories",
                total=len(analyses),
                status="Starting...",
                details="",
            )

            # Write markdown files for each repository analysis
            success_count = 0
            fail_count = 0

            for i, a in enumerate(analyses):
                path = output_path / f"{a.repo_name}.md"

                # Update progress
                details = f"Processing {a.repo_name}"
                progress.update(
                    task,
                    completed=i + 1,
                    status=f"{i + 1}/{len(analyses)}",
                    details=details,
                )

                try:
                    with open(path, "w") as f:
                        f.write(f"# {a.repo_name}\n\n")
                        f.write("## Summary\n\n")
                        f.write(f"{a.summary}\n\n")

                        if "error" not in a.tags and "analysis-failed" not in a.tags:
                            # Only write these sections for successful analyses
                            f.write("## Strengths\n\n")
                            for strength in a.strengths:
                                f.write(f"- {strength}\n")
                            f.write("\n")

                            f.write("## Weaknesses\n\n")
                            for weakness in a.weaknesses:
                                f.write(f"- {weakness}\n")
                            f.write("\n")

                            if a.recommendations:
                                f.write("## Recommendations\n\n")
                                for rec in a.recommendations:
                                    f.write(
                                        f"- **{rec.recommendation}** ({rec.priority} Priority)  \n",
                                    )
                                    f.write(f"  *Reason: {rec.reason}*\n")
                                f.write("\n")

                            f.write("## Assessment\n\n")
                            f.write(f"- **Activity**: {a.activity_assessment}\n")
                            f.write(f"- **Value**: {a.estimated_value}\n")
                            f.write(f"- **Tags**: {', '.join(a.tags)}\n")
                            success_count += 1
                        else:
                            f.write(f"**Analysis failed**: {a.summary}\n")
                            fail_count += 1
                except Exception as e:
                    console.print(f"[red]Error writing report for {a.repo_name}: {e}")
                    fail_count += 1

            # Create summary report
            summary_path = output_path / "repositories_report.md"
            with open(summary_path, "w") as f:
                # Add single repo mode indicator if applicable
                if settings.single_repo:
                    f.write("# Single Repository Analysis Report\n\n")
                    f.write(
                        f"*This report contains analysis for a single repository: **{settings.single_repo}**.*\n\n",
                    )
                else:
                    f.write("# Repository Analysis Summary\n\n")

                f.write("## Overview\n\n")
                f.write(f"- **Total Repositories**: {len(analyses)}\n")
                f.write(f"- **Successfully Analyzed**: {success_count}\n")
                f.write(f"- **Failed Analyses**: {fail_count}\n")

                # Add mode information
                if settings.single_repo:
                    f.write(
                        f"- **Mode**: Single repository analysis of **{settings.single_repo}**\n",
                    )
                else:
                    f.write("- **Mode**: Full repository analysis\n")
                f.write("\n")

                f.write("## Repositories\n\n")

                for a in analyses:
                    value_icon = (
                        "🔴"
                        if a.estimated_value == "Low"
                        else "🟡"
                        if a.estimated_value == "Medium"
                        else "🟢"
                    )
                    status = (
                        "✅" if "error" not in a.tags and "analysis-failed" not in a.tags else "❌"
                    )

                    f.write(f"### {a.repo_name} {value_icon} {status}\n\n")
                    f.write(f"_{a.summary}_\n\n")
                    f.write(f"- **Activity**: {a.activity_assessment}\n")
                    f.write(f"- **Value**: {a.estimated_value}\n")
                    f.write(f"- **Tags**: {', '.join(a.tags)}\n\n")

            # Show final results
            if not quiet:
                console.print("\n[bold green]Analysis complete![/]")

                # Create content for panel with mode information
                panel_content = f"Total Repositories: {len(analyses)}\nSuccessfully Analyzed: {success_count}\nFailed Analyses: {fail_count}"

                # Add mode information
                if settings.single_repo:
                    panel_content += (
                        f"\nMode: Single repository analysis of [bold]{settings.single_repo}[/]"
                    )
                    panel_title = "Single Repository Analysis"
                else:
                    panel_content += "\nMode: Full repository analysis"
                    panel_title = "Repository Analysis Summary"

                console.print(
                    Panel(
                        panel_content,
                        title=panel_title,
                        border_style="green",
                        expand=False,
                    ),
                )

                # Show output location
                console.print(
                    f"\nReports generated in: [bold]{output_path.absolute()}[/]",
                )
            else:
                # Just print the output path in quiet mode
                console.print(f"{output_path.absolute()}")

        except KeyboardInterrupt:
            console.print("\n[bold yellow]Operation cancelled by user.[/]")
            raise typer.Exit(code=1)
        except Exception as e:
            console.print(f"\n[bold red]Error during analysis:[/] {e}")
            if debug:
                import traceback

                console.print(traceback.format_exc())
            raise typer.Exit(code=1)


@app.command()
@authenticate_command("cleanup")
def cleanup(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force removal of all files without confirmation.",
    ),
    output_dir: str | None = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Directory containing analysis results to clean up (default: .out/repos).",
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimize console output."),
    username: str | None = None,  # Added by with_auth_option, manually included here for clarity
):
    """Clean up generated repository analysis files."""
    # Get settings directly from the config module
    settings = load_settings()
    output_dir = output_dir or settings.output_dir
    output_path = Path(output_dir)

    if not output_path.exists():
        if not quiet:
            console.print(f"[yellow]No output directory found at {output_path}[/]")
        raise typer.Exit(code=0)

    # Count files to delete
    files = list(output_path.glob("*.md"))
    if not files:
        if not quiet:
            console.print(f"[yellow]No analysis files found in {output_path}[/]")
        raise typer.Exit(code=0)

    # Ask for confirmation if not forced
    if not force and not quiet:
        delete_confirmed = typer.confirm(
            f"Delete {len(files)} analysis files from {output_path}?",
            default=False,
        )
        if not delete_confirmed:
            console.print("[yellow]Operation cancelled.[/]")
            raise typer.Exit(code=0)

    # Delete files with progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Cleaning up..."),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        disable=quiet,
    ) as progress:
        task = progress.add_task("[red]Deleting files", total=len(files))

        for file in files:
            if file.name != "repositories_report.md":  # Preserve report if needed
                try:
                    file.unlink()
                except Exception as e:
                    console.print(f"[red]Error deleting {file.name}: {e}[/]")
            progress.update(task, advance=1)

    if not quiet:
        console.print(
            f"[bold green]Successfully cleaned up {len(files)} analysis files![/]",
        )


@app.command()
def logs(
    latest: bool = typer.Option(
        True,
        "--latest",
        "-l",
        help="Show only the latest log file.",
    ),
    all_logs: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Show a list of all available log files.",
    ),
    log_file: str | None = typer.Option(
        None,
        "--file",
        "-f",
        help="Specific log file to display.",
    ),
):
    """View analysis log files."""
    # Get logs directory from settings
    settings = load_settings()
    logs_dir = settings.logs_dir

    # Ensure logs directory exists
    if not os.path.exists(logs_dir):
        console.print(f"[yellow]Logs directory not found: {logs_dir}[/]")
        return

    # Get all log files
    log_files = sorted(
        [f for f in os.listdir(logs_dir) if f.startswith("analysis_log_")],
        reverse=True,
    )

    if not log_files:
        console.print("[yellow]No log files found.[/]")
        return

    # Show list of all log files
    if all_logs:
        table = Table(title="Available Log Files")
        table.add_column("Filename", style="cyan")
        table.add_column("Date", style="green")
        table.add_column("Time", style="green")
        table.add_column("Size", style="blue", justify="right")

        for file in log_files:
            # Extract date and time from filename
            try:
                parts = file.replace("analysis_log_", "").replace(".txt", "").split("_")
                if len(parts) >= 2:
                    date = parts[0]
                    time = parts[1]
                else:
                    date = "Unknown"
                    time = "Unknown"
            except Exception:  # Be specific about the exception
                date = "Unknown"
                time = "Unknown"

            # Get file size
            size = os.path.getsize(os.path.join(logs_dir, file))
            size_str = f"{size / 1024:.1f} KB" if size > 1024 else f"{size} bytes"

            table.add_row(file, date, time, size_str)

        console.print(table)
        return

    # Determine which log file to show
    file_to_show = None
    if log_file:
        if log_file in log_files:
            file_to_show = log_file
        else:
            # Check if partial name was provided
            matches = [f for f in log_files if log_file in f]
            if len(matches) == 1:
                file_to_show = matches[0]
            elif len(matches) > 1:
                console.print(
                    f"[yellow]Multiple log files match '{log_file}'. Please be more specific:[/]",
                )
                for match in matches[:5]:  # Show at most 5 matches
                    console.print(f"  {match}")
                if len(matches) > 5:
                    console.print(f"  ... and {len(matches) - 5} more")
                return
            else:
                console.print(f"[red]Log file not found: {log_file}[/]")
                return
    elif latest:
        file_to_show = log_files[0] if log_files else None

    if not file_to_show:
        console.print("[yellow]No log file specified or found.[/]")
        return

    # Display the log file
    log_path = os.path.join(logs_dir, file_to_show)
    try:
        with open(log_path) as f:
            content = f.read()

        # Create syntax highlighted content
        syntax = Syntax(content, "text", theme="monokai", line_numbers=True)

        console.print(
            Panel(
                syntax,
                title=f"Log File: {file_to_show}",
                subtitle=f"Path: {log_path}",
                expand=False,
            ),
        )
    except Exception as e:
        console.print(f"[red]Error reading log file: {e}[/]")


@app.command()
def reports(
    summary: bool = typer.Option(
        True,
        "--summary",
        "-s",
        help="Show the summary report of all repositories.",
    ),
    repository: str | None = typer.Option(
        None,
        "--repo",
        "-r",
        help="Show the report for a specific repository.",
    ),
    list_reports: bool = typer.Option(
        False,
        "--list",
        "-l",
        help="List all available repository reports.",
    ),
):
    """View repository analysis reports."""
    # Get output directory from settings
    settings = load_settings()
    output_dir = settings.output_dir

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        console.print(f"[yellow]Reports directory not found: {output_dir}[/]")
        return

    # Get all report files
    report_files = [f for f in os.listdir(output_dir) if f.endswith(".md")]

    if not report_files:
        console.print("[yellow]No report files found.[/]")
        return

    # List all report files
    if list_reports:
        table = Table(title="Available Repository Reports")
        table.add_column("Repository", style="cyan")
        table.add_column("Size", style="green", justify="right")
        table.add_column("Last Modified", style="blue")

        for file in sorted(report_files):
            # Skip the main summary report
            if file == "repositories_report.md":
                continue

            # Get repo name from filename
            repo_name = file.replace(".md", "")

            # Get file details
            file_path = os.path.join(output_dir, file)
            size = os.path.getsize(file_path)
            size_str = f"{size / 1024:.1f} KB" if size > 1024 else f"{size} bytes"

            # Get last modified time
            mod_time = os.path.getmtime(file_path)
            mod_time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(mod_time))

            table.add_row(repo_name, size_str, mod_time_str)

        console.print(table)
        return

    # Show report for a specific repository
    if repository:
        # Check if report exists directly
        report_file = f"{repository}.md"
        if report_file not in report_files:
            # Try fuzzy match
            matches = [f for f in report_files if repository.lower() in f.lower()]
            if len(matches) == 1:
                report_file = matches[0]
            elif len(matches) > 1:
                console.print(
                    f"[yellow]Multiple reports match '{repository}'. Please be more specific:[/]",
                )
                for match in matches[:10]:  # Show at most 10 matches
                    console.print(f"  {match.replace('.md', '')}")
                if len(matches) > 10:
                    console.print(f"  ... and {len(matches) - 10} more")
                return
            else:
                console.print(f"[red]No report found for repository: {repository}[/]")
                return

        # Display the repository report
        report_path = os.path.join(output_dir, report_file)
        try:
            with open(report_path) as f:
                content = f.read()

            # Create syntax highlighted content
            syntax = Syntax(content, "markdown", theme="monokai")

            console.print(
                Panel(
                    syntax,
                    title=f"Repository Report: {report_file.replace('.md', '')}",
                    subtitle=f"Path: {report_path}",
                    expand=False,
                ),
            )
        except Exception as e:
            console.print(f"[red]Error reading report file: {e}[/]")
        return

    # Show summary report
    if summary:
        summary_path = os.path.join(output_dir, "repositories_report.md")
        if not os.path.exists(summary_path):
            console.print("[yellow]Summary report not found. Run analysis first.[/]")
            return

        try:
            with open(summary_path) as f:
                content = f.read()

            # Create syntax highlighted content
            syntax = Syntax(content, "markdown", theme="monokai")

            console.print(
                Panel(
                    syntax,
                    title="Repository Analysis Summary",
                    subtitle=f"Path: {summary_path}",
                    expand=False,
                ),
            )
        except Exception as e:
            console.print(f"[red]Error reading summary report: {e}[/]")


@app.command()
@authenticate_command("reset")
def reset(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force removal without confirmation.",
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimize console output."),
    username: str | None = None,  # Added by with_auth_option, manually included here for clarity
):
    """Reset and clean up all analysis files, removing reports that don't match your GitHub repositories."""
    # Get settings directly from the config module
    settings = load_settings()
    output_dir = settings.output_dir
    output_path = Path(output_dir)

    # Get the user's GitHub username
    github_username = settings.github_username

    if not quiet:
        console.print(f"[bold blue]GitHub Username:[/] {github_username}")

    if not output_path.exists():
        if not quiet:
            console.print(f"[yellow]No output directory found at {output_path}[/]")
        raise typer.Exit(code=0)

    # Count files to delete
    report_files = list(output_path.glob("*.md"))
    if not report_files:
        if not quiet:
            console.print(f"[yellow]No analysis files found in {output_path}[/]")
        raise typer.Exit(code=0)

    # Fetch the user's actual repositories
    try:
        # Import necessary classes here to avoid circular imports
        from repo_organizer.infrastructure.github_rest import GitHubRestAdapter
        from repo_organizer.utils.logger import Logger
        from repo_organizer.utils.rate_limiter import RateLimiter

        # Create rate limiter and logger for the GitHub adapter
        logger = Logger(
            str(output_path / "analysis.log"),
            console,
            debug_enabled=False,
            quiet_mode=quiet,
        )
        github_lim = RateLimiter(settings.github_rate_limit, name="GitHub")

        # Create the GitHub adapter
        github = GitHubRestAdapter(
            github_username=github_username,
            github_token=settings.github_token,
            rate_limiter=github_lim,
            logger=logger,
        )

        # Use the adapter to get repositories
        repos = github.get_repositories(limit=settings.max_repos)
        repo_names = {repo.name for repo in repos}

        # Identify reports that don't belong to the user's repositories
        invalid_reports = []
        for file_path in report_files:
            repo_name = file_path.stem
            # Skip the main report file
            if repo_name == "repositories_report":
                continue

            if repo_name not in repo_names:
                invalid_reports.append(file_path)

        if not invalid_reports:
            if not quiet:
                console.print("[green]No invalid repository reports found.[/]")
            raise typer.Exit(code=0)

        # Show what will be deleted
        if not quiet:
            console.print(
                f"[yellow]Found {len(invalid_reports)} repository reports that don't match your GitHub repositories:[/]",
            )
            for file_path in invalid_reports[:10]:
                console.print(f"  • {file_path.name}")
            if len(invalid_reports) > 10:
                console.print(f"  • ... and {len(invalid_reports) - 10} more")

        # Ask for confirmation
        if not force and not quiet:
            delete_confirmed = typer.confirm(
                f"Delete these {len(invalid_reports)} files?",
                default=False,
            )
            if not delete_confirmed:
                console.print("[yellow]Operation cancelled.[/]")
                raise typer.Exit(code=0)

        # Delete the invalid files
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Cleaning up invalid reports..."),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            disable=quiet,
        ) as progress:
            task = progress.add_task("[red]Deleting files", total=len(invalid_reports))

            for file_path in invalid_reports:
                try:
                    file_path.unlink()
                    progress.advance(task)
                except Exception as e:
                    console.print(f"[red]Error deleting {file_path.name}: {e}[/]")

        # Also remove the summary report so it will be regenerated
        summary_path = output_path / "repositories_report.md"
        if summary_path.exists():
            try:
                summary_path.unlink()
                if not quiet:
                    console.print("[green]Removed summary report for regeneration.[/]")
            except Exception as e:
                console.print(f"[red]Error removing summary report: {e}[/]")

        if not quiet:
            console.print(
                f"[bold green]Successfully removed {len(invalid_reports)} invalid repository reports![/]",
            )

    except Exception as e:
        console.print(f"[bold red]Error resetting repository files: {e}[/]")
        if logger and getattr(logger, "debug_enabled", False):
            import traceback

            console.print(traceback.format_exc())
        raise typer.Exit(code=1)


@app.command()
@authenticate_command("execute_actions")
def actions(
    action_type: ActionType = typer.Option(
        ActionType.ALL,
        "--type",
        "-t",
        help="Type of action to execute.",
    ),
    dry_run: bool = typer.Option(
        True,
        "--dry-run",
        "-d",
        help="Perform a dry run without making changes.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompts.",
    ),
    output_dir: str | None = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Override the output directory.",
    ),
    username: str | None = None,  # Added by with_auth_option, manually included here for clarity
):
    """Execute repository actions based on analysis results.

    This command uses the recommended actions from repository analyses to perform
    operations like archiving, deleting, extracting valuable parts, or pinning
    repositories. By default, it runs in dry-run mode to show what would happen.
    """
    try:
        # Pass the action type as string or None for ALL
        action = None if action_type == ActionType.ALL else action_type.value.upper()

        # Execute actions
        execute_actions(
            dry_run=dry_run,
            force=force,
            output_dir=output_dir,
            action_type=action,
            username=username,
        )
    except Exception as e:
        console.print(f"[bold red]Error executing actions: {e}[/]")
        if getattr(e, "__cause__", None):
            console.print(f"[red]Caused by: {e.__cause__}[/]")
        import traceback

        console.print(traceback.format_exc(), style="red")
        raise typer.Exit(code=1)


app.add_typer(dev_app, name="dev")


if __name__ == "__main__":
    app()
