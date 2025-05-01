"""Domain objects and ports related to *source control* / GitHub.

This bounded context deals with everything required to **retrieve** source
code metadata – independent of the concrete technology (GitHub REST, GitHub
CLI, Git, GitLab, Bitbucket, etc.).

Keeping the domain model free from infrastructure-specific details enables
easier testing, clearer boundaries and strict adherence to the Dependency
Inversion Principle (DIP).
"""

# Re-export most commonly used names for convenience
from .models import Commit, Contributor, LanguageBreakdown, Repository
from .protocols import SourceControlPort

__all__ = [
    "Commit",
    "Contributor",
    "LanguageBreakdown",
    "Repository",
    "SourceControlPort",
]
