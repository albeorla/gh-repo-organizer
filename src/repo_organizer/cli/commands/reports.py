"""Report management commands for viewing and managing repository analysis reports."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from repo_organizer.infrastructure.config.settings import load_settings

# Create Typer app for report commands
reports_app = typer.Typer(
    name="reports",
    help="View and manage repository analysis reports.",
    short_help="Manage reports"
)

# Create console for rich output
console = Console()

@reports_app.command(name="list")
def list_reports():
    """List all available repository analysis reports."""
    settings = load_settings()
    output_path = Path(settings.output_dir)

    if not output_path.exists():
        console.print("[yellow]No reports found. Run 'repo analyze' first.[/]")
        raise typer.Exit(1)

    # Create a table to display reports
    table = Table(title="Available Repository Reports")
    table.add_column("Repository", style="cyan")
    table.add_column("Last Updated", style="green")
    table.add_column("Status", style="blue")

    # Find all report files
    report_files = list(output_path.glob("**/report.md"))
    if not report_files:
        console.print("[yellow]No reports found. Run 'repo analyze' first.[/]")
        raise typer.Exit(1)

    # Add reports to table
    for report_file in sorted(report_files):
        repo_name = report_file.parent.name
        last_updated = report_file.stat().st_mtime
        status = "Complete"  # Could be enhanced to show actual status
        
        from datetime import datetime
        updated_str = datetime.fromtimestamp(last_updated).strftime("%Y-%m-%d %H:%M:%S")
        
        table.add_row(repo_name, updated_str, status)

    console.print(table)

@reports_app.command()
def show(
    repository: str = typer.Argument(..., help="Name of the repository to show report for."),
    format: str = typer.Option(
        "markdown",
        "--format",
        "-f",
        help="Output format (markdown or plain).",
    ),
):
    """Show the analysis report for a specific repository."""
    settings = load_settings()
    output_path = Path(settings.output_dir)
    report_path = output_path / repository / "report.md"

    if not report_path.exists():
        console.print(
            f"[red]No report found for repository '{repository}'. "
            "Run 'repo analyze' first.[/]"
        )
        raise typer.Exit(1)

    # Read and display the report
    report_content = report_path.read_text()
    
    if format.lower() == "markdown":
        syntax = Syntax(report_content, "markdown", theme="monokai")
        console.print(syntax)
    else:
        console.print(report_content)

@reports_app.command()
def summary():
    """Show a summary of all repository analysis reports."""
    settings = load_settings()
    output_path = Path(settings.output_dir)

    if not output_path.exists():
        console.print("[yellow]No reports found. Run 'repo analyze' first.[/]")
        raise typer.Exit(1)

    # Create a table for the summary
    table = Table(title="Repository Analysis Summary")
    table.add_column("Repository", style="cyan")
    table.add_column("Status", style="blue")
    table.add_column("Issues", style="red")
    table.add_column("Recommendations", style="green")

    # Find all summary files
    summary_files = list(output_path.glob("**/summary.json"))
    if not summary_files:
        console.print("[yellow]No summaries found. Run 'repo analyze' first.[/]")
        raise typer.Exit(1)

    # Add summaries to table
    import json
    for summary_file in sorted(summary_files):
        repo_name = summary_file.parent.name
        try:
            with open(summary_file) as f:
                data = json.load(f)
                status = data.get("status", "Unknown")
                issues = str(len(data.get("issues", [])))
                recommendations = str(len(data.get("recommendations", [])))
                table.add_row(repo_name, status, issues, recommendations)
        except Exception as e:
            console.print(f"[red]Error reading summary for {repo_name}: {str(e)}[/]")
            continue

    console.print(table) 