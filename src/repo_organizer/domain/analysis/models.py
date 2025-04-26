"""Domain model for repository *analysis* results.

The analysis bounded context essentially lives *entirely* in memory – there is
no notion of persistence at the domain level.  Therefore, simple immutable
dataclasses are more than enough and do not require the heavier runtime cost
of Pydantic validation.  However, the existing LangChain prompt & parser
implementation relies on **Pydantic** models for JSON schema enforcement.  To
avoid a large rewrite in this phase we *wrap* the existing Pydantic
``RepoAnalysis`` while still providing an idiomatic dataclass façade for the
application & domain layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from repo_organizer.models.repo_models import RepoAnalysis as _RepoAnalysisPydantic
from repo_organizer.models.repo_models import RepoRecommendation as _RecommendationPydantic


# ---------------------------------------------------------------------------
# Value Objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Recommendation:
    """Concrete action item for improving a repository."""

    recommendation: str
    reason: str
    priority: str  # High / Medium / Low

    # Conversion helpers -----------------------------------------------------
    @staticmethod
    def from_pydantic(pyd_obj: _RecommendationPydantic) -> "Recommendation":
        return Recommendation(
            recommendation=pyd_obj.recommendation,
            reason=pyd_obj.reason,
            priority=pyd_obj.priority,
        )

    def to_pydantic(self) -> _RecommendationPydantic:  # noqa: D401
        return _RecommendationPydantic(
            recommendation=self.recommendation,
            reason=self.reason,
            priority=self.priority,
        )


# ---------------------------------------------------------------------------
# Aggregate Root
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RepoAnalysis:
    """Aggregate representing the *outcome* of analysing one repository."""

    repo_name: str
    summary: str
    strengths: Sequence[str]
    weaknesses: Sequence[str]
    recommendations: Sequence[Recommendation]
    activity_assessment: str
    estimated_value: str
    tags: Sequence[str]

    # Conversion helpers -----------------------------------------------------
    @staticmethod
    def from_pydantic(pyd_obj: _RepoAnalysisPydantic) -> "RepoAnalysis":
        return RepoAnalysis(
            repo_name=pyd_obj.repo_name,
            summary=pyd_obj.summary,
            strengths=list(pyd_obj.strengths),
            weaknesses=list(pyd_obj.weaknesses),
            recommendations=[Recommendation.from_pydantic(r) for r in pyd_obj.recommendations],
            activity_assessment=pyd_obj.activity_assessment,
            estimated_value=pyd_obj.estimated_value,
            tags=list(pyd_obj.tags),
        )

    def to_pydantic(self) -> _RepoAnalysisPydantic:  # noqa: D401
        return _RepoAnalysisPydantic(
            repo_name=self.repo_name,
            summary=self.summary,
            strengths=list(self.strengths),
            weaknesses=list(self.weaknesses),
            recommendations=[rec.to_pydantic() for rec in self.recommendations],
            activity_assessment=self.activity_assessment,
            estimated_value=self.estimated_value,
            tags=list(self.tags),
        )
