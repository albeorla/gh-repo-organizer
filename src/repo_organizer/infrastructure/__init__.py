"""Infrastructure-level adapters (outbound)."""

from .github_rest import GitHubRestAdapter  # noqa: F401

__all__ = ["GitHubRestAdapter"]

# Export analysis adapter for convenience
from .langchain_claude import LangChainClaudeAdapter  # noqa: E402 F401

__all__.append("LangChainClaudeAdapter")

