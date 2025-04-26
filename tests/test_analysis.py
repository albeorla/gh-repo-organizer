"""
Tests for the repository analysis functionality.
"""

import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

from repo_organizer.models.repo_models import RepoAnalysis, RepoRecommendation
from repo_organizer.services.llm_service import LLMService
from repo_organizer.services.repository_analyzer_service import RepositoryAnalyzerService


class TestRepositoryAnalysis(unittest.TestCase):
    """Tests for the repository analysis functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.fixtures_dir = Path(__file__).parent / "fixtures"
        self.sample_repo_data = self._load_json_fixture("sample_repo_data.json")
        
        # Create a temporary output directory for test files
        self.test_output_dir = Path(__file__).parent / "test_output"
        os.makedirs(self.test_output_dir, exist_ok=True)

    def tearDown(self):
        """Clean up test artifacts."""
        import shutil
        if self.test_output_dir.exists():
            shutil.rmtree(self.test_output_dir)

    def _load_json_fixture(self, filename):
        """Load a JSON fixture file."""
        with open(self.fixtures_dir / filename, "r") as f:
            return json.load(f)

    @patch("repo_organizer.services.llm_service.ChatAnthropic")
    def test_llm_service_analysis(self, mock_anthropic):
        """Test LLM service produces valid analysis."""
        # Setup mock LLM response
        mock_message = MagicMock()
        mock_message.content = json.dumps({
            "repo_name": "youtube_playlist_organizer",
            "summary": "This repository contains a tool for organizing and managing YouTube playlists.",
            "strengths": ["Provides a comprehensive set of playlist management features"],
            "weaknesses": ["Limited community engagement"],
            "recommendations": [
                {
                    "recommendation": "Add comprehensive test suite",
                    "reason": "Ensuring reliability and preventing regressions",
                    "priority": "High"
                }
            ],
            "activity_assessment": "Moderate",
            "estimated_value": "Medium",
            "tags": ["youtube-api", "playlist-management"]
        })
        
        mock_anthropic.return_value.invoke.return_value = mock_message
        
        # Initialize LLM service and test analysis
        llm_service = LLMService("dummy_api_key")
        result = llm_service.analyze_repository(self.sample_repo_data)
        
        # Verify result
        self.assertIsInstance(result, RepoAnalysis)
        self.assertEqual(result.repo_name, "youtube_playlist_organizer")
        self.assertIn("YouTube playlists", result.summary)
        self.assertIsInstance(result.recommendations[0], RepoRecommendation)
        self.assertEqual(result.estimated_value, "Medium")

    @patch("repo_organizer.services.repository_analyzer_service.LLMService")
    def test_repository_analyzer_service(self, mock_llm_service):
        """Test repository analyzer service end-to-end."""
        # Setup mock LLM service
        mock_analysis = RepoAnalysis(
            repo_name="youtube_playlist_organizer",
            summary="This repository contains a tool for organizing and managing YouTube playlists.",
            strengths=["Provides a comprehensive set of playlist management features"],
            weaknesses=["Limited community engagement"],
            recommendations=[
                RepoRecommendation(
                    recommendation="Add comprehensive test suite",
                    reason="Ensuring reliability and preventing regressions",
                    priority="High"
                )
            ],
            activity_assessment="Moderate",
            estimated_value="Medium",
            tags=["youtube-api", "playlist-management"]
        )
        
        mock_llm_instance = MagicMock()
        mock_llm_instance.analyze_repository.return_value = mock_analysis
        mock_llm_service.return_value = mock_llm_instance
        
        # Initialize repository analyzer service
        service = RepositoryAnalyzerService(
            output_dir=str(self.test_output_dir),
            api_key="dummy_api_key",
            llm_service=mock_llm_instance
        )
        
        # Test analysis
        result = service.analyze_repository(self.sample_repo_data)
        
        # Verify result
        self.assertEqual(result.repo_name, "youtube_playlist_organizer")
        self.assertEqual(result.estimated_value, "Medium")
        
        # Test report generation
        service._write_single_report(result, self.sample_repo_data)
        
        # Verify report file was created
        report_path = self.test_output_dir / "youtube_playlist_organizer.md"
        self.assertTrue(report_path.exists())
        
        # Verify report content
        with open(report_path, "r") as f:
            content = f.read()
            self.assertIn("# youtube_playlist_organizer", content)
            self.assertIn("## Analysis Summary", content)
            self.assertIn("Add comprehensive test suite", content)


if __name__ == "__main__":
    unittest.main()