"""Infrastructure-level adapters (outbound).

The Infrastructure layer contains concrete implementations of the interfaces
defined in the Domain layer. Instead of importing through this file, import
directly from the specific adapter modules to avoid circular dependencies.

Examples:
    from repo_organizer.infrastructure.github_rest import GitHubRestAdapter
    from repo_organizer.infrastructure.analysis.langchain_claude_adapter import (
        LangChainClaudeAdapter,
    )
"""

__all__ = []
