"""Repository management commands for analyzing and organizing GitHub repositories."""

import os
from pathlib import Path
from typing import Optional

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

from repo_organizer.cli.auth_middleware import authenticate_command
from repo_organizer.infrastructure.analysis.langchain_claude_adapter import (
    LangChainClaudeAdapter,
)
from repo_organizer.infrastructure.config.settings import load_settings
from repo_organizer.infrastructure.github_rest import GitHubRestAdapter
from repo_organizer.utils.logger import Logger
from repo_organizer.utils.rate_limiter import RateLimiter

# Create Typer app for repo commands
repo_app = typer.Typer(
    name="repo",
    help="Repository management commands for analyzing and organizing GitHub repositories.",
    short_help="Manage repositories",
)

# Create console for rich output
console = Console()


@repo_app.command()
@authenticate_command("analyze")
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
    max_repos: Optional[int] = typer.Option(
        None,
        "--max-repos",
        "-m",
        help="Maximum number of repositories to analyze (deprecated, use --limit).",
    ),
    owner: str = typer.Option(None, "--owner", help="GitHub owner/user to analyze."),
    single_repo: Optional[str] = typer.Option(
        None,
        "--single-repo",
        "-s",
        help="Process only a single repository by name.",
    ),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug logging."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimize console output."),
    username: Optional[str] = None,  # Added by with_auth_option
):
    """Analyze GitHub repositories and generate detailed reports.

    This command uses Domain-Driven Design (DDD) architecture to provide accurate
    repository analysis with proper separation of concerns, improved error handling,
    and better maintainability.
    """
    # For backwards compatibility
    if max_repos is not None and limit is None:
        limit = max_repos

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
        progress.add_task(
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

            # Analyze repositories using the application service
            from repo_organizer.application.analyze_repositories import analyze_repositories

            analyze_repositories(
                github=github,
                llm=llm,
                output_dir=output_path,
                force=force,
                limit=limit,
                progress=progress,
                logger=logger,
            )

        except Exception as e:
            logger.error(f"Error during repository analysis: {e!s}")
            if debug:
                import traceback

                logger.debug(traceback.format_exc())
            raise typer.Exit(1)


@repo_app.command()
@authenticate_command("cleanup")
def cleanup(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force removal of all files without confirmation.",
    ),
    output_dir: Optional[str] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Directory containing analysis results to clean up (default: .out/repos).",
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimize console output."),
    username: Optional[str] = None,  # Added by with_auth_option
):
    """Clean up analysis files and cached data.

    This command removes analysis results, logs, and cached data from previous runs.
    Use with caution as this operation cannot be undone.
    """
    settings = load_settings()

    # Resolve output directory
    if output_dir is None:
        output_path = Path(settings.output_dir)
    else:
        expanded_output = os.path.abspath(
            os.path.expanduser(os.path.expandvars(output_dir)),
        )
        output_path = Path(expanded_output)

    if not output_path.exists():
        if not quiet:
            console.print(
                f"[yellow]Output directory does not exist: {output_path}[/]",
            )
        return

    # Get confirmation unless force flag is used
    if not force:
        confirm = typer.confirm(
            f"This will remove all files in {output_path}. Continue?",
            default=False,
        )
        if not confirm:
            if not quiet:
                console.print("[yellow]Operation cancelled.[/]")
            return

    # Remove all files in the output directory
    import shutil

    try:
        shutil.rmtree(output_path)
        if not quiet:
            console.print(
                f"[green]Successfully removed all files in {output_path}[/]",
            )
    except Exception as e:
        console.print(f"[red]Error removing files: {e!s}[/]")
        raise typer.Exit(1)


@repo_app.command()
@authenticate_command("reset")
def reset(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force removal without confirmation.",
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimize console output."),
    username: Optional[str] = None,  # Added by with_auth_option
):
    """Reset the application state by removing all generated files.

    This command removes all analysis results, logs, and cached data,
    effectively resetting the application to its initial state.
    Use with extreme caution as this operation cannot be undone.
    """
    settings = load_settings()
    output_path = Path(settings.output_dir)

    # Get confirmation unless force flag is used
    if not force:
        console.print(
            Panel(
                "[bold red]WARNING: This will remove all analysis results and cached data.[/]\n"
                "This operation cannot be undone.",
                title="Reset Confirmation",
                border_style="red",
            ),
        )
        confirm = typer.confirm("Are you sure you want to continue?", default=False)
        if not confirm:
            if not quiet:
                console.print("[yellow]Operation cancelled.[/]")
            return

    # Remove output directory and its contents
    if output_path.exists():
        import shutil

        try:
            shutil.rmtree(output_path)
            if not quiet:
                console.print(
                    f"[green]Successfully removed output directory: {output_path}[/]",
                )
        except Exception as e:
            console.print(f"[red]Error removing output directory: {e!s}[/]")
            raise typer.Exit(1)

    # Remove any other application state files here
    # For example: cached credentials, temporary files, etc.

    if not quiet:
        console.print("[green]Application state has been reset successfully.[/]")
