"""Repository action commands for executing and managing repository actions."""

from enum import Enum
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from repo_organizer.cli.auth_middleware import authenticate_command
from repo_organizer.cli.commands.actions_executor import execute_actions
from repo_organizer.infrastructure.config.settings import load_settings

# Create Typer app for action commands
actions_app = typer.Typer(
    name="actions", help="Execute and manage repository actions.", short_help="Manage actions"
)

# Create console for rich output
console = Console()


# Define Enum for action types
class ActionType(str, Enum):
    """Repository action types."""

    DELETE = "delete"
    ARCHIVE = "archive"
    EXTRACT = "extract"
    KEEP = "keep"
    PIN = "pin"
    ALL = "all"


@actions_app.command()
@authenticate_command("execute_actions")
def execute(
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
    username: str | None = None,  # Added by with_auth_option
):
    """Execute repository actions based on analysis results."""
    settings = load_settings()

    # Resolve output directory
    if output_dir is None:
        output_path = Path(settings.output_dir)
    else:
        import os

        expanded_output = os.path.abspath(
            os.path.expanduser(os.path.expandvars(output_dir)),
        )
        output_path = Path(expanded_output)

    if not output_path.exists():
        console.print("[yellow]No analysis results found. Run 'repo analyze' first.[/]")
        raise typer.Exit(1)

    # Get confirmation for non-dry-run operations
    if not dry_run and not force:
        console.print(
            Panel(
                "[bold red]WARNING: This will make changes to your GitHub repositories.[/]\n"
                "Some actions cannot be undone.",
                title="Action Confirmation",
                border_style="red",
            ),
        )
        confirm = typer.confirm("Are you sure you want to continue?", default=False)
        if not confirm:
            console.print("[yellow]Operation cancelled.[/]")
            return

    # Execute actions
    try:
        execute_actions(
            action_type=action_type.value,
            dry_run=dry_run,
            output_dir=output_path,
            github_token=settings.github_token,
            github_username=settings.github_username,
        )
    except Exception as e:
        console.print(f"[red]Error executing actions: {e!s}[/]")
        raise typer.Exit(1)


@actions_app.command(name="list")
def list_actions():
    """List all available repository actions."""
    settings = load_settings()
    output_path = Path(settings.output_dir)

    if not output_path.exists():
        console.print("[yellow]No analysis results found. Run 'repo analyze' first.[/]")
        raise typer.Exit(1)

    # Create a table to display actions
    table = Table(title="Available Repository Actions")
    table.add_column("Repository", style="cyan")
    table.add_column("Action", style="green")
    table.add_column("Reason", style="blue")

    # Find all action files
    action_files = list(output_path.glob("**/actions.json"))
    if not action_files:
        console.print("[yellow]No actions found. Run 'repo analyze' first.[/]")
        raise typer.Exit(1)

    # Add actions to table
    import json

    for action_file in sorted(action_files):
        repo_name = action_file.parent.name
        try:
            with open(action_file) as f:
                data = json.load(f)
                for action in data.get("actions", []):
                    action_type = action.get("type", "unknown")
                    reason = action.get("reason", "No reason provided")
                    table.add_row(repo_name, action_type, reason)
        except Exception as e:
            console.print(f"[red]Error reading actions for {repo_name}: {e!s}[/]")
            continue

    console.print(table)


@actions_app.command(name="dry-run")
def dry_run(
    action_type: ActionType = typer.Option(
        ActionType.ALL,
        "--type",
        "-t",
        help="Type of action to simulate.",
    ),
    output_dir: str | None = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Override the output directory.",
    ),
):
    """Simulate repository actions without making changes."""
    settings = load_settings()

    # Resolve output directory
    if output_dir is None:
        output_path = Path(settings.output_dir)
    else:
        import os

        expanded_output = os.path.abspath(
            os.path.expanduser(os.path.expandvars(output_dir)),
        )
        output_path = Path(expanded_output)

    if not output_path.exists():
        console.print("[yellow]No analysis results found. Run 'repo analyze' first.[/]")
        raise typer.Exit(1)

    # Execute actions in dry-run mode
    try:
        execute_actions(
            action_type=action_type.value,
            dry_run=True,
            output_dir=output_path,
            github_token=settings.github_token,
            github_username=settings.github_username,
        )
    except Exception as e:
        console.print(f"[red]Error simulating actions: {e!s}[/]")
        raise typer.Exit(1)
