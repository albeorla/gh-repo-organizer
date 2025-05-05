#!/usr/bin/env python
"""
Test script to fetch all repositories for a user, including private ones.

This script provides a simple way to test GitHub authentication and repository 
fetching capabilities of the repo-organizer tool.

Usage:
    poetry run python scripts/fetch_all_repos.py --username YOUR_GITHUB_USERNAME

Make sure to set the GITHUB_TOKEN environment variable with a valid GitHub 
personal access token that has the 'repo' scope.
"""

import os
import sys
import argparse
from pathlib import Path

# Add the src directory to the Python path to allow imports
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from repo_organizer.infrastructure.github_rest import GitHubRestAdapter
from repo_organizer.utils.logger import Logger
from repo_organizer.utils.rate_limiter import RateLimiter
from repo_organizer.infrastructure.config.settings import load_settings


def main():
    """Fetch all repositories for a GitHub user, including private ones."""
    parser = argparse.ArgumentParser(description="Fetch all repositories for a GitHub user")
    parser.add_argument("--username", required=True, help="GitHub username")
    parser.add_argument("--token", help="GitHub token (optional, will use GITHUB_TOKEN env var if not provided)")
    parser.add_argument("--limit", type=int, default=100, help="Maximum number of repositories to fetch")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Get token from args or environment
    github_token = args.token or os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("ERROR: GitHub token not provided. Set GITHUB_TOKEN environment variable or use --token")
        return 1
    
    # Create simple console logger
    class ConsoleLogger:
        def __init__(self, verbose=False):
            self.verbose = verbose
            
        def log(self, message, level="info"):
            if level == "error":
                print(f"ERROR: {message}")
            elif level == "warning":
                print(f"WARNING: {message}")
            elif self.verbose or level != "info":
                print(message)
    
    logger = ConsoleLogger(args.verbose)
    
    # Create rate limiter
    rate_limiter = RateLimiter(30, name="GitHub")
    
    # Create GitHub adapter
    github = GitHubRestAdapter(
        github_username=args.username,
        github_token=github_token,
        rate_limiter=rate_limiter,
        logger=logger,
    )
    
    print(f"Fetching up to {args.limit} repositories for {args.username}...")
    
    # Fetch repositories
    repos = github.get_repositories(limit=args.limit)
    
    # Display results
    public_repos = [repo for repo in repos if not getattr(repo, "is_private", False)]
    private_repos = [repo for repo in repos if getattr(repo, "is_private", False)]
    
    print(f"\nFound {len(repos)} total repositories:")
    print(f"  - Public: {len(public_repos)}")
    print(f"  - Private: {len(private_repos)}")
    
    # Print repository names
    print("\nRepositories:")
    for i, repo in enumerate(repos, 1):
        privacy = "[PRIVATE]" if getattr(repo, "is_private", False) else "[PUBLIC]"
        print(f"{i:3d}. {privacy} {repo.name}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())