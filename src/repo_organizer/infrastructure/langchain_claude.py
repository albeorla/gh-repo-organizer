"""
LangChain/Anthropic adapter implementing the ``AnalyzerPort`` interface.

This module is deprecated and will be moved to the analysis-specific adapter location:
infrastructure/analysis/langchain_claude_adapter.py
"""

from __future__ import annotations

from typing import Mapping

from repo_organizer.domain.analysis.models import RepoAnalysis
from repo_organizer.domain.analysis.protocols import AnalyzerPort
from repo_organizer.infrastructure.analysis.llm_service import LLMService


class LangChainClaudeAdapter(LLMService, AnalyzerPort):
    """Concrete adapter delegating to the existing ``LLMService`` implementation.

    The class simply *inherits* from ``LLMService`` to reuse all existing logic
    while providing a domain-layer friendly ``analyze`` method that returns a
    *domain* ``RepoAnalysis`` instance (dataclass) rather than the Pydantic
    model currently produced by the legacy service.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "claude-3-7-sonnet-latest",
        temperature: float = 0.2,
        thinking_enabled: bool = True,
        thinking_budget: int = 16000,
        rate_limiter=None,
        logger=None,
    ):
        """Initialize with extended thinking support.

        Args:
            api_key: Anthropic API key
            model_name: Model identifier (default: claude-3-7-sonnet-latest)
            temperature: LLM temperature (0.0-1.0)
            thinking_enabled: Whether to enable extended thinking
            thinking_budget: Token budget for thinking
            rate_limiter: Optional rate limiter
            logger: Optional logger
        """
        super().__init__(
            api_key=api_key,
            model_name=model_name,
            temperature=temperature,
            thinking_enabled=thinking_enabled,
            thinking_budget=thinking_budget,
            rate_limiter=rate_limiter,
            logger=logger,
        )

    # ------------------------------------------------------------------
    # AnalyzerPort implementation
    # ------------------------------------------------------------------

    def analyze(self, repo_data: Mapping[str, object]) -> RepoAnalysis:  # type: ignore[override]
        try:
            pyd_model = super().analyze_repository(dict(repo_data))
            # Convert to domain dataclass
            from repo_organizer.domain.analysis.models import (
                RepoAnalysis as _DomainRepoAnalysis,
            )

            return _DomainRepoAnalysis.from_pydantic(pyd_model)
        except Exception as e:
            # Print a more informative error message
            if hasattr(self, "logger") and self.logger:
                self.logger.log(f"Error during analysis with LLM: {e}", "error")
                if hasattr(e, "__cause__") and e.__cause__:
                    self.logger.log(f"Root cause: {e.__cause__}", "error")

            # Create a fallback analysis for the repository
            fallback_name = repo_data.get("repo_name", "unknown")

            # Try to create a minimal analysis with what we know
            return RepoAnalysis(
                repo_name=fallback_name,
                summary=f"Analysis failed: {str(e)}",
                strengths=["Analysis unavailable"],
                weaknesses=["Analysis unavailable"],
                recommendations=[],
                activity_assessment="Unknown (analysis failed)",
                estimated_value="Unknown (analysis failed)",
                tags=["error", "analysis-failed"],
            )
