"""CLI command implementations for repository actions.

This module has been refactored and replaced by the commands/ directory structure.
The execute_actions function has been moved to repo_organizer.cli.commands.actions_executor.

This module is kept for backward compatibility but will be removed in a future version.
"""

from repo_organizer.cli.commands.actions_executor import execute_actions

__all__ = ["execute_actions"]
