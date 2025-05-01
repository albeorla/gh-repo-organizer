"""Ports (Protocols) for the *Analysis* bounded context."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Mapping

    from .models import RepoAnalysis


class AnalyzerPort(Protocol):
    """Abstract interface for analysing repositories using an LLM or rules."""

    def analyze(self, repo_data: Mapping[str, object]) -> RepoAnalysis:
        """Return analysis for *repo_data*.

        ``repo_data`` is a *flat* mapping prepared by the application layer.
        The exact keys are an implementation detail of the adapter.
        """
