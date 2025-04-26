"""
Domain models for GitHub repository analysis.
"""

from pydantic import BaseModel, Field


class LanguageBreakdown(BaseModel):
    """Breakdown of programming languages used in a repository."""

    language: str = Field(description="Programming language name")
    percentage: float = Field(description="Percentage of code in this language")


class RepoRecommendation(BaseModel):
    """Recommendations for a repository."""

    recommendation: str = Field(
        description="Specific recommendation for the repository"
    )
    reason: str = Field(description="Reason for the recommendation")
    priority: str = Field(description="Priority level (High, Medium, Low)")


class RepoAnalysis(BaseModel):
    """Comprehensive analysis of a GitHub repository."""

    repo_name: str = Field(description="Name of the repository")
    summary: str = Field(
        description="Brief summary of the repository's purpose and function"
    )
    strengths: list[str] = Field(description="Key strengths of the repository")
    weaknesses: list[str] = Field(description="Areas that could be improved")
    recommendations: list[RepoRecommendation] = Field(
        description="Specific recommendations"
    )
    activity_assessment: str = Field(
        description="Assessment of repository activity level"
    )
    estimated_value: str = Field(
        description="Estimated value/importance of the repository (High, Medium, Low)"
    )
    tags: list[str] = Field(description="Suggested tags/categories for the repository")


class RepoInfo(BaseModel):
    """Basic information about a GitHub repository."""

    name: str
    description: str | None = None
    url: str | None = None
    updated_at: str | None = None
    is_archived: bool = False
    stars: int = 0
    forks: int = 0


class Commit(BaseModel):
    """Git commit information."""

    hash: str
    message: str
    author: str
    date: str


class Contributor(BaseModel):
    """Repository contributor information."""

    name: str
    commits: int
