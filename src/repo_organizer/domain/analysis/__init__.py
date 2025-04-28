"""Domain objects and ports for the *Analysis* bounded context."""

from .models import RepoAnalysis, Recommendation
from .protocols import AnalyzerPort
from .services import AnalysisService
from .action_recommendation_service import ActionRecommendationService
from .repository_analyzer_service import RepositoryAnalyzerService
from .value_objects import (
    RecommendedAction,
    ActivityLevel,
    ValueLevel,
    PriorityLevel,
    RepoAssessment,
)
from .events import (
    RepositoryAnalysisCompleted,
    RepositoryActionRecommended,
    HighPriorityIssueIdentified,
    AnalysisError,
)

__all__ = [
    # Models
    "RepoAnalysis",
    "Recommendation",
    # Protocols
    "AnalyzerPort",
    # Services
    "AnalysisService",
    "ActionRecommendationService",
    "RepositoryAnalyzerService",
    # Value Objects
    "RecommendedAction",
    "ActivityLevel",
    "ValueLevel",
    "PriorityLevel",
    "RepoAssessment",
    # Events
    "RepositoryAnalysisCompleted",
    "RepositoryActionRecommended",
    "HighPriorityIssueIdentified",
    "AnalysisError",
]
