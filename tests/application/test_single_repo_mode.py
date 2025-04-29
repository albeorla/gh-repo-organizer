"""
Test the single repository limitation mode functionality.
"""

import pytest
from unittest.mock import MagicMock, patch

from repo_organizer.application.analyze_repositories import analyze_repositories
from repo_organizer.domain.source_control.models import Repository


@pytest.fixture
def mock_source_control():
    """Create a mock source control adapter."""
    mock = MagicMock()
    
    # Create sample repositories
    repos = [
        Repository(
            name="repo1",
            description="Test repository 1",
            url="https://github.com/test/repo1",
            updated_at="2025-04-29T12:00:00Z",
            is_archived=False,
            stars=10,
            forks=5,
        ),
        Repository(
            name="repo2",
            description="Test repository 2",
            url="https://github.com/test/repo2",
            updated_at="2025-04-28T12:00:00Z",
            is_archived=False,
            stars=20,
            forks=10,
        ),
        Repository(
            name="repo3",
            description="Test repository 3",
            url="https://github.com/test/repo3",
            updated_at="2025-04-27T12:00:00Z",
            is_archived=True,
            stars=5,
            forks=2,
        ),
    ]
    
    # Configure the mock to return the sample repositories
    mock.list_repositories.return_value = repos
    mock.fetch_languages.return_value = []
    mock.get_repository_readme.return_value = "Sample README content"
    mock.recent_commits.return_value = []
    
    # Add a logger attribute to the mock
    mock.logger = MagicMock()
    
    return mock


@pytest.fixture
def mock_analyzer():
    """Create a mock analyzer."""
    mock = MagicMock()
    
    # Configure the mock to return a sample analysis
    def mock_analyze(repo_data):
        from repo_organizer.domain.analysis.models import RepoAnalysis
        
        return RepoAnalysis(
            repo_name=repo_data["repo_name"],
            summary=f"Analysis of {repo_data['repo_name']}",
            strengths=["Sample strength"],
            weaknesses=["Sample weakness"],
            recommendations=[],
            activity_assessment="Medium",
            estimated_value="Medium",
            tags=["test"],
        )
    
    mock.analyze.side_effect = mock_analyze
    
    return mock


def test_analyze_repositories_normal_mode(mock_source_control, mock_analyzer):
    """Test analyze_repositories without single repository mode."""
    # Call the function without specifying a single repository
    results = analyze_repositories("testuser", mock_source_control, mock_analyzer)
    
    # Verify all repositories were processed
    assert len(results) == 3
    assert [r.repo_name for r in results] == ["repo1", "repo2", "repo3"]
    
    # Verify the list_repositories was called correctly
    mock_source_control.list_repositories.assert_called_once_with("testuser", limit=None)


def test_analyze_repositories_single_repo_mode(mock_source_control, mock_analyzer):
    """Test analyze_repositories with single repository mode."""
    # Call the function with a single repository specified
    results = analyze_repositories("testuser", mock_source_control, mock_analyzer, single_repo="repo2")
    
    # Verify only the specified repository was processed
    assert len(results) == 1
    assert results[0].repo_name == "repo2"
    
    # Verify that filtering was logged
    mock_source_control.logger.log.assert_any_call("Filtering repositories to only include: repo2")


def test_analyze_repositories_single_repo_not_found(mock_source_control, mock_analyzer):
    """Test analyze_repositories with a non-existent repository."""
    # Call the function with a non-existent repository
    results = analyze_repositories("testuser", mock_source_control, mock_analyzer, single_repo="non-existent-repo")
    
    # Verify no repositories were processed
    assert len(results) == 0
    
    # Verify that error was logged
    mock_source_control.logger.log.assert_any_call(
        "Repository 'non-existent-repo' not found in list of 3 repositories", 
        level="error"
    )