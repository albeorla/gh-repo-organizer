"""
LangChain/Anthropic adapter implementing the ``AnalyzerPort`` interface.

This is a composition-based adapter following DDD principles to keep the domain
layer independent of external frameworks.
"""

from __future__ import annotations

from typing import Mapping, Optional, Any

from repo_organizer.domain.analysis.models import RepoAnalysis
from repo_organizer.domain.analysis.protocols import AnalyzerPort
from repo_organizer.infrastructure.analysis.llm_service import LLMService
from repo_organizer.utils.logger import Logger
from repo_organizer.utils.rate_limiter import RateLimiter


class LangChainClaudeAdapter(AnalyzerPort):
    """
    Adapter that implements the AnalyzerPort using LangChain and Claude.

    This adapter uses composition rather than inheritance, properly separating
    the domain interface from the infrastructure implementation.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "claude-3-7-sonnet-latest",
        temperature: float = 0.2,
        thinking_enabled: bool = True,
        thinking_budget: int = 16000,
        rate_limiter: Optional[RateLimiter] = None,
        logger: Optional[Logger] = None,
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
        # Use composition instead of inheritance
        self._llm_service = LLMService(
            api_key=api_key,
            model_name=model_name,
            temperature=temperature,
            thinking_enabled=thinking_enabled,
            thinking_budget=thinking_budget,
            rate_limiter=rate_limiter,
            logger=logger,
        )
        self.logger = logger

    # ------------------------------------------------------------------
    # AnalyzerPort implementation
    # ------------------------------------------------------------------

    def analyze(self, repo_data: Mapping[str, Any]) -> RepoAnalysis:
        """
        Analyze a repository using Claude LLM.

        Args:
            repo_data: A mapping containing repository data

        Returns:
            A domain model RepoAnalysis object
        """
        try:
            # Use the LLM service to get a Pydantic model
            pyd_model = self._llm_service.analyze_repository(dict(repo_data))

            # Convert to domain dataclass
            from repo_organizer.domain.analysis.models import (
                RepoAnalysis as DomainRepoAnalysis,
            )

            return DomainRepoAnalysis.from_pydantic(pyd_model)
        except Exception as e:
            # Print a more informative error message
            if self.logger:
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
