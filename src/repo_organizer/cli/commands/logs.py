"""Log management commands for viewing and managing application logs."""

from pathlib import Path

import typer
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from repo_organizer.infrastructure.config.settings import load_settings

# Create Typer app for log commands
logs_app = typer.Typer(
    name="logs", help="View and manage application logs.", short_help="Manage logs"
)

# Create console for rich output
console = Console()


@logs_app.command()
def latest():
    """Show the latest log file."""
    settings = load_settings()
    output_path = Path(settings.output_dir)
    log_path = output_path / "analysis.log"

    if not log_path.exists():
        console.print("[yellow]No log file found. Run 'repo analyze' first.[/]")
        raise typer.Exit(1)

    # Read and display the log
    log_content = log_path.read_text()
    syntax = Syntax(log_content, "log", theme="monokai")
    console.print(syntax)


@logs_app.command(name="all")
def list_all():
    """List all available log files."""
    settings = load_settings()
    output_path = Path(settings.output_dir)

    if not output_path.exists():
        console.print("[yellow]No logs found. Run 'repo analyze' first.[/]")
        raise typer.Exit(1)

    # Create a table to display logs
    table = Table(title="Available Log Files")
    table.add_column("File", style="cyan")
    table.add_column("Size", style="green")
    table.add_column("Last Updated", style="blue")

    # Find all log files
    log_files = list(output_path.glob("**/*.log"))
    if not log_files:
        console.print("[yellow]No logs found. Run 'repo analyze' first.[/]")
        raise typer.Exit(1)

    # Add logs to table
    for log_file in sorted(log_files):
        file_name = log_file.relative_to(output_path)
        size = log_file.stat().st_size
        last_updated = log_file.stat().st_mtime

        from datetime import datetime

        updated_str = datetime.fromtimestamp(last_updated).strftime("%Y-%m-%d %H:%M:%S")

        # Format size
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.1f} MB"

        table.add_row(str(file_name), size_str, updated_str)

    console.print(table)


@logs_app.command()
def view(
    file: str = typer.Argument(..., help="Log file to view (relative to output directory)."),
    tail: int = typer.Option(
        None,
        "--tail",
        "-n",
        help="Show only the last N lines.",
    ),
    follow: bool = typer.Option(
        False,
        "--follow",
        "-f",
        help="Follow log output (like tail -f).",
    ),
):
    """View a specific log file."""
    settings = load_settings()
    output_path = Path(settings.output_dir)
    log_path = output_path / file

    if not log_path.exists():
        console.print(f"[red]Log file not found: {file}[/]")
        raise typer.Exit(1)

    if follow:
        import time

        last_size = 0
        try:
            while True:
                current_size = log_path.stat().st_size
                if current_size > last_size:
                    with open(log_path) as f:
                        f.seek(last_size)
                        new_content = f.read()
                        console.print(new_content, end="", markup=False)
                    last_size = current_size
                time.sleep(0.1)
        except KeyboardInterrupt:
            return
    else:
        # Read and display the log
        log_content = log_path.read_text().splitlines()

        if tail:
            log_content = log_content[-tail:]

        syntax = Syntax("\n".join(log_content), "log", theme="monokai")
        console.print(syntax)
