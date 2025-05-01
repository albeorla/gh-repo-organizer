"""Domain objects and ports for the *Analysis* bounded context."""

from .action_recommendation_service import ActionRecommendationService
from .events import (
    AnalysisError,
    HighPriorityIssueIdentified,
    RepositoryActionRecommended,
    RepositoryAnalysisCompleted,
)
from .models import Recommendation, RepoAnalysis
from .protocols import AnalyzerPort
from .repository_analyzer_service import RepositoryAnalyzerService
from .services import AnalysisService
from .value_objects import (
    ActivityLevel,
    PriorityLevel,
    RecommendedAction,
    RepoAssessment,
    ValueLevel,
)

__all__ = [
    "ActionRecommendationService",
    "ActivityLevel",
    "AnalysisError",
    # Services
    "AnalysisService",
    # Protocols
    "AnalyzerPort",
    "HighPriorityIssueIdentified",
    "PriorityLevel",
    "Recommendation",
    # Value Objects
    "RecommendedAction",
    # Models
    "RepoAnalysis",
    "RepoAssessment",
    "RepositoryActionRecommended",
    # Events
    "RepositoryAnalysisCompleted",
    "RepositoryAnalyzerService",
    "ValueLevel",
]
