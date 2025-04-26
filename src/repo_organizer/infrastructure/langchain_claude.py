"""LangChain/Anthropic adapter implementing the ``AnalyzerPort`` interface."""

from __future__ import annotations

from typing import Mapping

from repo_organizer.domain.analysis.models import RepoAnalysis
from repo_organizer.domain.analysis.protocols import AnalyzerPort
from repo_organizer.services.llm_service import LLMService


class LangChainClaudeAdapter(LLMService, AnalyzerPort):
    """Concrete adapter delegating to the existing ``LLMService`` implementation.

    The class simply *inherits* from ``LLMService`` to reuse all existing logic
    while providing a domain-layer friendly ``analyze`` method that returns a
    *domain* ``RepoAnalysis`` instance (dataclass) rather than the Pydantic
    model currently produced by the legacy service.
    """

    # ------------------------------------------------------------------
    # AnalyzerPort implementation
    # ------------------------------------------------------------------

    def analyze(self, repo_data: Mapping[str, object]) -> RepoAnalysis:  # type: ignore[override]
        pyd_model = super().analyze_repository(dict(repo_data))
        # Convert to domain dataclass
        from repo_organizer.domain.analysis.models import RepoAnalysis as _DomainRepoAnalysis

        return _DomainRepoAnalysis.from_pydantic(pyd_model)
