"""Tests for analyze_repo.py script."""

import pytest
import tempfile
import json
from pathlib import Path
from scripts.analyze_repo import parse_repository_input, generate_analysis_report

def test_parse_repository_input_github_url():
    """Test parsing a GitHub URL."""
    input_str = "https://github.com/username/repo-name"
    owner, repo = parse_repository_input(input_str)
    assert owner == "username"
    assert repo == "repo-name"

def test_parse_repository_input_github_url_with_git_extension():
    """Test parsing a GitHub URL with .git extension."""
    input_str = "https://github.com/username/repo-name.git"
    owner, repo = parse_repository_input(input_str)
    assert owner == "username"
    assert repo == "repo-name"

def test_parse_repository_input_owner_repo_format():
    """Test parsing an owner/repo format string."""
    input_str = "username/repo-name"
    owner, repo = parse_repository_input(input_str)
    assert owner == "username"
    assert repo == "repo-name"

def test_parse_repository_input_invalid_format():
    """Test parsing an invalid input format."""
    input_str = "invalid-format"
    with pytest.raises(ValueError):
        parse_repository_input(input_str)

def test_parse_repository_input_with_additional_path():
    """Test parsing a GitHub URL with additional path."""
    input_str = "https://github.com/username/repo-name/tree/main"
    owner, repo = parse_repository_input(input_str)
    assert owner == "username"
    assert repo == "repo-name"

def test_generate_analysis_report():
    """Test the analysis report generation function."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as tmp:
        tmp_file = Path(tmp.name)
        
        # Test data
        repo_name = "test-repo"
        repo_data = {
            "name": "test-repo",
            "description": "Test repository description",
            "url": "https://github.com/username/test-repo",
            "updated_at": "2023-05-01T12:00:00Z",
            "stars": 42,
            "forks": 10
        }
        analysis = {
            "summary": "This is a test summary of the repository",
            "strengths": ["Good documentation", "Active community"],
            "weaknesses": ["Missing tests", "Outdated dependencies"],
            "recommendations": [
                {
                    "recommendation": "Add more tests",
                    "reason": "Improve code quality",
                    "priority": "High"
                }
            ],
            "activity_assessment": "Active",
            "estimated_value": "Medium",
            "tags": ["python", "testing"],
            "recommended_action": "KEEP"
        }
        language_breakdown = "Python: 80.0%, JavaScript: 20.0%"
        recent_commits_count = 5
        
        # Generate the report
        generate_analysis_report(
            output_file=tmp_file,
            repo_name=repo_name,
            repo_data=repo_data,
            analysis=analysis,
            language_breakdown=language_breakdown,
            recent_commits_count=recent_commits_count
        )
        
        # Read the generated report
        with open(tmp_file, 'r') as f:
            content = f.read()
        
        # Check the report content
        assert f"# {repo_name}" in content
        assert "This is a test summary of the repository" in content
        assert "Good documentation" in content
        assert "Active community" in content
        assert "Missing tests" in content
        assert "Outdated dependencies" in content
        assert "Add more tests" in content
        assert "Improve code quality" in content
        assert "High Priority" in content
        assert "Activity**: Active" in content
        assert "Value**: Medium" in content
        assert "Tags**: python, testing" in content
        assert "Recommended Action**: KEEP" in content
        assert "Python: 80.0%, JavaScript: 20.0%" in content
        assert "Recent Activity**: 5 recent commits" in content
        
        # Clean up
        tmp_file.unlink()

def test_generate_analysis_report_missing_fields():
    """Test the analysis report generation with missing fields."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as tmp:
        tmp_file = Path(tmp.name)
        
        # Minimal test data
        repo_name = "minimal-repo"
        repo_data = {
            "description": "Minimal description",
            "url": "",
            "updated_at": "",
            "stars": 0,
            "forks": 0
        }
        analysis = {
            "summary": "Minimal summary"
            # Missing other fields
        }
        language_breakdown = ""
        recent_commits_count = 0
        
        # Generate the report
        generate_analysis_report(
            output_file=tmp_file,
            repo_name=repo_name,
            repo_data=repo_data,
            analysis=analysis,
            language_breakdown=language_breakdown,
            recent_commits_count=recent_commits_count
        )
        
        # Read the generated report
        with open(tmp_file, 'r') as f:
            content = f.read()
        
        # Check the report content has default values for missing fields
        assert f"# {repo_name}" in content
        assert "Minimal summary" in content
        assert "No strengths identified" in content
        assert "No weaknesses identified" in content
        assert "Activity**: Unknown" in content
        assert "Value**: Unknown" in content
        assert "Tags**: none" in content
        
        # Clean up
        tmp_file.unlink()