"""Development commands for the CLI."""

import subprocess
import sys

import typer

dev_app = typer.Typer(help="Development commands")


@dev_app.command()
def lint():
    """Run ruff check on the codebase."""
    result = subprocess.run(["ruff", "check", "."], check=False)
    sys.exit(result.returncode)


@dev_app.command()
def format():
    """Run ruff format on the codebase."""
    result = subprocess.run(["ruff", "format", "."], check=False)
    sys.exit(result.returncode)


@dev_app.command()
def check():
    """Run all checks (lint, format, test)."""
    exit_code = 0

    print("Running linting checks...")
    exit_code |= subprocess.run(["ruff", "check", "."], check=False).returncode

    print("\nChecking code formatting...")
    exit_code |= subprocess.run(
        ["ruff", "format", ".", "--check"],
        check=False,
    ).returncode

    print("\nRunning tests...")
    exit_code |= subprocess.run(["pytest", "tests/"], check=False).returncode

    sys.exit(exit_code)
