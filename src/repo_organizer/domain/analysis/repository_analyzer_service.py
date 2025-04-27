"""
Domain service for orchestrating repository analysis.

This module contains the RepositoryAnalyzerService which coordinates the analysis
of repositories using the analyzer and GitHub service.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional, Sequence, Callable

from repo_organizer.domain.analysis.models import RepoAnalysis
from repo_organizer.domain.core.models import Repository
from repo_organizer.domain.source_control.github_service import GitHubService
from repo_organizer.domain.analysis.analyzer import RepositoryAnalyzer

logger = logging.getLogger(__name__)

class RepositoryAnalyzerService:
    """
    Service that orchestrates repository analysis.
    
    This service coordinates between the GitHub service and repository analyzer
    to analyze repositories and generate reports.
    """
    
    def __init__(
        self,
        output_dir: str | Path,
        api_key: str,
        github_service: GitHubService,
        analyzer: RepositoryAnalyzer,
        max_repos: Optional[int] = None,
        debug: bool = False,
        repo_filter: Optional[Callable[[Repository], bool]] = None,
        force_reanalyze: bool = False,
    ):
        """
        Initialize the repository analyzer service.
        
        Args:
            output_dir: Directory to write analysis reports to
            api_key: API key for the analyzer
            github_service: Service for interacting with GitHub
            analyzer: The repository analyzer to use
            max_repos: Maximum number of repositories to analyze, or None for no limit
            debug: Whether to enable debug logging
            repo_filter: Optional filter function for repositories
            force_reanalyze: Whether to reanalyze repositories that already have reports
        """
        self.output_dir = Path(output_dir)
        self.api_key = api_key
        self.github_service = github_service
        self.analyzer = analyzer
        self.max_repos = max_repos
        self.debug = debug
        self.repo_filter = repo_filter
        self.force_reanalyze = force_reanalyze
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Configure logging
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
            
    def should_analyze_repo(self, repo: Repository) -> bool:
        """
        Determine if a repository should be analyzed.
        
        Args:
            repo: The repository to check
            
        Returns:
            True if the repository should be analyzed
        """
        # Skip if filtered out
        if self.repo_filter and not self.repo_filter(repo):
            logger.debug(f"Skipping {repo.name} - filtered out")
            return False
            
        # Check if report already exists
        report_path = self.output_dir / f"{repo.name}.json"
        if report_path.exists() and not self.force_reanalyze:
            logger.debug(f"Skipping {repo.name} - report exists")
            return False
            
        return True
        
    def analyze_repository(self, repo: Repository) -> Optional[RepoAnalysis]:
        """
        Analyze a single repository.
        
        Args:
            repo: The repository to analyze
            
        Returns:
            The repository analysis if successful, None if analysis fails
        """
        try:
            logger.info(f"Analyzing repository: {repo.name}")
            
            # Prepare data for analysis
            data = self.prepare_analysis_data(repo)
            
            # Run analysis
            analysis = self.analyzer.analyze(data)
            
            # Write report
            self.write_report(repo.name, analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing {repo.name}: {str(e)}")
            if self.debug:
                logger.exception(e)
            return None
            
    def prepare_analysis_data(self, repo: Repository) -> dict:
        """
        Prepare repository data for analysis.
        
        Args:
            repo: The repository to prepare data for
            
        Returns:
            Dictionary of data for analysis
        """
        # Get additional data from GitHub
        contributors = self.github_service.get_contributors(repo)
        issues = self.github_service.get_issues(repo)
        pull_requests = self.github_service.get_pull_requests(repo)
        
        return {
            "name": repo.name,
            "description": repo.description,
            "created_at": repo.created_at,
            "updated_at": repo.updated_at,
            "contributors": contributors,
            "issues": issues,
            "pull_requests": pull_requests,
        }
        
    def write_report(self, repo_name: str, analysis: RepoAnalysis) -> None:
        """
        Write an analysis report to disk.
        
        Args:
            repo_name: Name of the repository
            analysis: The analysis to write
        """
        report_path = self.output_dir / f"{repo_name}.json"
        analysis.to_json(report_path)
        logger.debug(f"Wrote report to {report_path}")
        
    def generate_reports(self, repos: Sequence[Repository]) -> list[RepoAnalysis]:
        """
        Generate analysis reports for multiple repositories.
        
        Args:
            repos: The repositories to analyze
            
        Returns:
            List of successful analyses
        """
        analyses = []
        count = 0
        
        for repo in repos:
            # Check max repos limit
            if self.max_repos and count >= self.max_repos:
                logger.info(f"Reached max repos limit of {self.max_repos}")
                break
                
            # Check if repo should be analyzed
            if not self.should_analyze_repo(repo):
                continue
                
            # Analyze repo
            analysis = self.analyze_repository(repo)
            if analysis:
                analyses.append(analysis)
                count += 1
                
        return analyses 