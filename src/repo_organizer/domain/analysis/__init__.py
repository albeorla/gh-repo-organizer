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
