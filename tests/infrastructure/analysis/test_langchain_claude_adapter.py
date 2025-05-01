"""
Tests for the LangChainClaudeAdapter.

These tests mock the LLMService to avoid actual API calls.
"""

import pytest
from unittest.mock import MagicMock, patch
import json
from pathlib import Path

from repo_organizer.domain.analysis.models import RepoAnalysis
from repo_organizer.infrastructure.analysis.langchain_claude_adapter import (
    LangChainClaudeAdapter,
)
from repo_organizer.utils.exceptions import RateLimitExceededError


# Load sample data for testing
@pytest.fixture
def sample_repo_data():
    """Load sample repository data for testing."""
    fixtures_path = Path(__file__).parent.parent.parent / "fixtures"
    with open(fixtures_path / "sample_repo_data.json", "r") as f:
        return json.load(f)


@pytest.fixture
def mock_llm_service():
    """Create a mock LLMService that returns predetermined results."""
    mock = MagicMock()

    # Create a sample pydantic model
    from repo_organizer.infrastructure.analysis.pydantic_models import (
        RepoAnalysis as PydanticRepoAnalysis,
        RepoRecommendation,
    )

    mock_recommendation = RepoRecommendation(
        recommendation="Add tests",
        reason="Improve reliability",
        priority="High",
    )

    mock_analysis = PydanticRepoAnalysis(
        repo_name="test-repo",
        summary="A test repository",
        strengths=["Good documentation"],
        weaknesses=["No tests"],
        recommendations=[mock_recommendation],
        activity_assessment="Active",
        estimated_value="High",
        tags=["test", "sample"],
        recommended_action="KEEP",
        action_reasoning="Good project worth keeping",
    )

    mock.analyze_repository.return_value = mock_analysis
    return mock


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    mock = MagicMock()
    mock.log = MagicMock()
    mock.debug_enabled = False
    return mock

@pytest.fixture
def adapter(mock_llm_service, mock_logger):
    """Create a LangChainClaudeAdapter with a mocked LLMService."""
    # Create the adapter with a dummy API key and the mock logger
    adapter = LangChainClaudeAdapter(
        api_key="fake-api-key",
        model_name="claude-3-7-sonnet-latest",
        temperature=0.2,
        thinking_enabled=True,
        thinking_budget=10000,
        logger=mock_logger,
    )
    
    # Replace the internal LLM service with our mock
    adapter._llm_service = mock_llm_service
    
    return adapter


class TestLangChainClaudeAdapter:
    """Test suite for the LangChainClaudeAdapter."""

    def test_analyze_success(self, adapter, sample_repo_data, mock_llm_service):
        """Test successful analysis of a repository."""
        # Analyze the repository
        result = adapter.analyze(sample_repo_data)

        # Verify mock was called
        assert mock_llm_service.analyze_repository.call_count == 1
        
        # Instead of checking exact argument equality, just verify that it was called with a dict
        # that contains the same repo_name - the adapter adds default values to the dict
        call_args = mock_llm_service.analyze_repository.call_args[0][0]
        assert isinstance(call_args, dict)
        assert call_args['repo_name'] == sample_repo_data['repo_name']

        # Check the result
        assert isinstance(result, RepoAnalysis)
        assert result.repo_name == "test-repo"
        assert result.summary == "A test repository"
        assert len(result.strengths) == 1
        assert result.strengths[0] == "Good documentation"
        assert len(result.weaknesses) == 1
        assert result.weaknesses[0] == "No tests"
        assert len(result.recommendations) == 1
        assert result.recommendations[0].recommendation == "Add tests"
        assert result.recommendations[0].priority == "High"
        assert result.activity_assessment == "Active"
        assert result.estimated_value == "High"
        assert len(result.tags) == 2
        assert "test" in result.tags

    def test_analyze_cache(self, adapter, sample_repo_data, mock_llm_service):
        """Test that caching works properly."""
        # First call should use the LLM service
        adapter.analyze(sample_repo_data)

        # Reset mock to verify second call doesn't use it
        mock_llm_service.analyze_repository.reset_mock()

        # Second call with same data should use cache
        adapter.analyze(sample_repo_data)

        # Verify the LLM service wasn't called again
        mock_llm_service.analyze_repository.assert_not_called()

        # Check cache metrics
        metrics = adapter.get_metrics()
        assert metrics["cache_hits"] == 1
        assert metrics["cache_misses"] == 1

    def test_analyze_rate_limit_error(
        self, adapter, sample_repo_data, mock_llm_service
    ):
        """Test handling of rate limit errors."""
        # Configure mock to raise rate limit error
        mock_llm_service.analyze_repository.side_effect = RateLimitExceededError(
            "Rate limit exceeded"
        )

        # Analyze should handle the error and return fallback
        result = adapter.analyze(sample_repo_data)

        # Check the result is a fallback
        assert isinstance(result, RepoAnalysis)
        assert "failed" in result.summary.lower()
        assert "error" in result.tags

        # Check metrics
        metrics = adapter.get_metrics()
        assert metrics["failed_requests"] == 1

    def test_analyze_general_error(self, adapter, sample_repo_data, mock_llm_service):
        """Test handling of general errors."""
        # Configure mock to raise general error
        mock_llm_service.analyze_repository.side_effect = Exception("General error")

        # Analyze should handle the error and return fallback
        result = adapter.analyze(sample_repo_data)

        # Check the result is a fallback
        assert isinstance(result, RepoAnalysis)
        assert "failed" in result.summary.lower()
        assert "error" in result.tags

        # Check metrics
        metrics = adapter.get_metrics()
        assert metrics["failed_requests"] == 1

    def test_retry_mechanism(self, adapter, sample_repo_data, mock_llm_service):
        """Test retry mechanism for transient errors."""
        # Set up mock to fail twice then succeed
        mock_llm_service.analyze_repository.side_effect = [
            Exception("First error"),
            Exception("Second error"),
            mock_llm_service.analyze_repository.return_value,
        ]

        # Override retry delay to speed up test
        adapter.retry_base_delay = 0.01

        # Analysis should succeed after retries
        result = adapter.analyze(sample_repo_data)

        # Verify mock was called 3 times (initial + 2 retries)
        assert mock_llm_service.analyze_repository.call_count == 3

        # Check the result is successful
        assert isinstance(result, RepoAnalysis)
        assert result.repo_name == "test-repo"

        # Check metrics
        metrics = adapter.get_metrics()
        assert metrics["successful_requests"] == 1
        assert metrics["failed_requests"] == 0  # Successful after retries
