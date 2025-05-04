#!/usr/bin/env python
"""
A script to analyze a GitHub repository directly from URL or owner/repo format.

This script accepts either a GitHub URL (https://github.com/owner/repo)
or an owner/repo string (owner/repo) as input, extracts the repository
information, and generates a detailed analysis report.

Usage:
    poetry run analyze-repo https://github.com/owner/repo
    poetry run analyze-repo owner/repo

The script will automatically extract the owner and repository name from the input,
fetch repository data from GitHub, analyze it using LLM, and generate a detailed report.
"""

import base64
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests

# Import necessary modules
from repo_organizer.infrastructure.config.settings import load_settings
from repo_organizer.utils.logger import Logger


def parse_repository_input(input_str: str) -> tuple[str, str]:
    """
    Parse repository input to extract owner and repo name.
    
    Accepts both GitHub URLs and owner/repo format.
    
    Args:
        input_str: Repository input string (URL or owner/repo)
        
    Returns:
        Tuple of (owner, repo_name)
        
    Raises:
        ValueError: If the input cannot be parsed into owner and repo name
    """
    # GitHub URL format (https://github.com/owner/repo)
    url_pattern = r"github\.com/([^/]+)/([^/]+)"
    url_match = re.search(url_pattern, input_str)
    
    if url_match:
        owner = url_match.group(1)
        repo = url_match.group(2)
        # Remove .git extension if present
        repo = repo.rstrip(".git")
        return owner, repo
    
    # Simple owner/repo format (owner/repo)
    simple_pattern = r"^([^/]+)/([^/]+)$"
    simple_match = re.search(simple_pattern, input_str)
    
    if simple_match:
        owner = simple_match.group(1)
        repo = simple_match.group(2)
        return owner, repo
    
    raise ValueError(
        "Invalid repository format. Use either a GitHub URL (https://github.com/owner/repo) "
        "or owner/repo format."
    )

def get_repository_info(github_username: str, repo_name: str, token: str | None = None, logger: Any | None = None) -> dict:
    """Get basic information about a repository."""
    url = f"https://api.github.com/repos/{github_username}/{repo_name}"
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            if logger:
                logger.log(f"Error fetching repository info: {response.status_code}", level="error")
            print(f"Error fetching repository info: {response.status_code}")
            return {}
        
        return response.json()
    except Exception as e:
        if logger:
            logger.log(f"Exception fetching repository info: {e}", level="error")
        print(f"Exception fetching repository info: {e}")
        return {}

def get_repository_readme(github_username: str, repo_name: str, token: str | None = None, logger: Any | None = None) -> str:
    """Get README content for a repository."""
    url = f"https://api.github.com/repos/{github_username}/{repo_name}/readme"
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            if logger:
                logger.log(f"Error fetching README: {response.status_code}", level="error")
            print(f"Error fetching README: {response.status_code}")
            return ""
        
        data = response.json()
        content = data.get("content", "")
        
        if content:
            try:
                decoded = base64.b64decode(content).decode("utf-8")
                return decoded
            except Exception as e:
                if logger:
                    logger.log(f"Error decoding README: {e}", level="error")
                print(f"Error decoding README: {e}")
                return ""
        
        return ""
    except Exception as e:
        if logger:
            logger.log(f"Exception fetching README: {e}", level="error")
        print(f"Exception fetching README: {e}")
        return ""

def get_repository_languages(github_username: str, repo_name: str, token: str | None = None, logger: Any | None = None) -> dict[str, float]:
    """Get language breakdown for a repository."""
    url = f"https://api.github.com/repos/{github_username}/{repo_name}/languages"
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            if logger:
                logger.log(f"Error fetching languages: {response.status_code}", level="error")
            print(f"Error fetching languages: {response.status_code}")
            return {}
        
        languages = response.json()
        
        # Calculate percentages
        total = sum(languages.values())
        if total == 0:
            return {}
        
        return {lang: round((count / total) * 100, 1) for lang, count in languages.items()}
    except Exception as e:
        if logger:
            logger.log(f"Exception fetching languages: {e}", level="error")
        print(f"Exception fetching languages: {e}")
        return {}

def get_repository_commits(github_username: str, repo_name: str, limit: int = 10, token: str | None = None, logger: Any | None = None) -> list[dict]:
    """Get recent commits for a repository."""
    url = f"https://api.github.com/repos/{github_username}/{repo_name}/commits"
    params = {"per_page": min(100, limit)}
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code != 200:
            if logger:
                logger.log(f"Error fetching commits: {response.status_code}", level="error")
            print(f"Error fetching commits: {response.status_code}")
            return []
        
        return response.json()[:limit]
    except Exception as e:
        if logger:
            logger.log(f"Exception fetching commits: {e}", level="error")
        print(f"Exception fetching commits: {e}")
        return []

def call_claude_api(api_key: str, model_name: str, prompt: str, max_tokens: int = 4000, logger: Any | None = None) -> dict:
    """Call the Anthropic Claude API directly."""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
        "x-api-key": api_key
    }
    
    data = {
        "model": model_name,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2
    }
    
    print(f"Calling Claude API with model {model_name}...")
    if logger:
        logger.log(f"Calling Claude API with model {model_name}")
    
    try:
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code != 200:
            if logger:
                logger.log(f"API error: {response.status_code}", level="error")
                logger.log(f"Response: {response.text}", level="error")
            print(f"API error: {response.status_code}")
            print(f"Response: {response.text}")
            return {}
        
        return response.json()
    except Exception as e:
        if logger:
            logger.log(f"Exception calling Claude API: {e}", level="error")
        print(f"Exception calling Claude API: {e}")
        return {}

def generate_analysis_report(
    output_file: Path,
    repo_name: str,
    repo_data: dict,
    analysis: dict,
    language_breakdown: str,
    recent_commits_count: int
) -> None:
    """
    Generate a detailed analysis report and write it to a markdown file.
    
    Args:
        output_file: The file path to write the report to
        repo_name: The name of the repository
        repo_data: The repository data
        analysis: The analysis results from Claude
        language_breakdown: The language breakdown string
        recent_commits_count: The number of recent commits
    """
    with open(output_file, "w") as f:
        # Write header and summary
        f.write(f"# {repo_name}\n\n")
        f.write("## Summary\n\n")
        f.write(f"{analysis.get('summary', 'No summary available')}\n\n")
        
        # Write repository information
        f.write("## Repository Information\n\n")
        f.write(f"- **Description**: {repo_data['description']}\n")
        f.write(f"- **URL**: {repo_data['url']}\n")
        f.write(f"- **Last Updated**: {repo_data['updated_at']}\n")
        f.write(f"- **Stars**: {repo_data['stars']}\n")
        f.write(f"- **Forks**: {repo_data['forks']}\n")
        f.write(f"- **Languages**: {language_breakdown}\n")
        f.write(f"- **Recent Activity**: {recent_commits_count} recent commits\n\n")
        
        # Write strengths
        f.write("## Strengths\n\n")
        for strength in analysis.get('strengths', ['No strengths identified']):
            f.write(f"- {strength}\n")
        f.write("\n")
        
        # Write weaknesses
        f.write("## Weaknesses\n\n")
        for weakness in analysis.get('weaknesses', ['No weaknesses identified']):
            f.write(f"- {weakness}\n")
        f.write("\n")
        
        # Write recommendations
        recommendations = analysis.get('recommendations', [])
        if recommendations:
            f.write("## Recommendations\n\n")
            for rec in recommendations:
                f.write(f"- **{rec['recommendation']}** ({rec['priority']} Priority)  \n")
                f.write(f"  *Reason: {rec['reason']}*\n")
            f.write("\n")
        
        # Write assessment
        f.write("## Assessment\n\n")
        f.write(f"- **Activity**: {analysis.get('activity_assessment', 'Unknown')}\n")
        f.write(f"- **Value**: {analysis.get('estimated_value', 'Unknown')}\n")
        f.write(f"- **Tags**: {', '.join(analysis.get('tags', ['none']))}\n")
        
        # Add recommended action
        if 'recommended_action' in analysis:
            f.write(f"- **Recommended Action**: {analysis['recommended_action']}\n")

def format_analysis_prompt(repo_data: dict) -> str:
    """Format a prompt for repository analysis."""
    return f"""
You are an AI assistant specialized in analyzing GitHub repositories and generating detailed reports. Your task is to evaluate the repository named "{repo_data['name']}" based on its README content and provide valuable insights, recommendations, and a decision on the repository's future.

First, carefully read and analyze the following repository information:

Repository Information:
- Name: {repo_data['name']}
- Description: {repo_data['description']}
- URL: {repo_data['url']}
- Last Updated: {repo_data['updated_at']}
- Archived on GitHub: {repo_data['is_archived']}
- Stars: {repo_data['stars']}
- Forks: {repo_data['forks']}
- Programming Languages: {repo_data['languages']}

Activity Information:
- Open Issues: {repo_data['open_issues']}
- Closed Issues: {repo_data['closed_issues']}
- Recent Activity: {repo_data['activity_summary']}
- Recent Commits: {repo_data['recent_commits_count']}
- Contributors: {repo_data['contributor_summary']}

Dependencies:
- {repo_data['dependency_info']}

README Content:
```markdown
{repo_data['readme_content']}
```

Based on this information, generate a detailed analysis in the following format:

```json
{{
  "summary": "Brief summary of the repository's purpose and function",
  "strengths": ["Strength 1", "Strength 2", "Strength 3"],
  "weaknesses": ["Weakness 1", "Weakness 2", "Weakness 3"],
  "recommendations": [
    {{
      "recommendation": "Specific recommendation 1",
      "reason": "Reason for recommendation 1",
      "priority": "High/Medium/Low"
    }},
    {{
      "recommendation": "Specific recommendation 2",
      "reason": "Reason for recommendation 2",
      "priority": "High/Medium/Low"
    }}
  ],
  "activity_assessment": "Assessment of repository activity (Active/Moderate/Low/Inactive)",
  "estimated_value": "High/Medium/Low",
  "tags": ["tag1", "tag2", "tag3"],
  "recommended_action": "KEEP/PIN/ARCHIVE/EXTRACT/DELETE"
}}
```

ONLY respond with a valid JSON object. No introductory text, no markdown formatting, no additional explanations.
"""

def analyze_repository(repo_input: str, github_token: str | None = None, output_dir: str = '.out/repos', logger: Any | None = None) -> None:
    """
    Analyze a repository from URL or owner/repo format.
    
    Args:
        repo_input: Repository URL or owner/repo string
        github_token: GitHub API token
        output_dir: Directory to save output
        logger: Logger instance
    """
    try:
        # Parse repository input
        username, repo_name = parse_repository_input(repo_input)
        
        if logger:
            logger.log(f"Analyzing repository: {username}/{repo_name}")
        print(f"Analyzing repository: {username}/{repo_name}")
        
        # Load settings
        settings = load_settings()
        
        # Setup output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Fetch repository data
        print(f"📊 Fetching repository information for {repo_name}...")
        repo_info = get_repository_info(username, repo_name, github_token, logger)
        if not repo_info:
            if logger:
                logger.log(f"Repository {username}/{repo_name} not found or inaccessible", level="error")
            print(f"\n❌ Repository {username}/{repo_name} not found or inaccessible")
            print("   Possible causes:")
            print("   - The repository does not exist")
            print("   - The repository is private and you don't have access")
            print("   - GitHub API rate limit exceeded")
            print("   - Network connection issues")
            print("\n💡 Tip: Check your GitHub token if the repository is private")
            return
        
        # Get README
        print(f"📄 Fetching README for {repo_name}...")
        readme_content = get_repository_readme(username, repo_name, github_token, logger)
        if not readme_content:
            print("   ⚠️ No README found or README is empty")
        
        # Get language breakdown
        print(f"🔤 Fetching language breakdown for {repo_name}...")
        languages = get_repository_languages(username, repo_name, github_token, logger)
        if languages:
            language_breakdown = ", ".join(f"{lang}: {percentage:.1f}%" for lang, percentage in languages.items())
            print(f"   Found: {language_breakdown}")
        else:
            language_breakdown = "No language information available"
            print("   ⚠️ No language information found")
        
        # Get commits
        print(f"📝 Fetching commit history for {repo_name}...")
        commits = get_repository_commits(username, repo_name, 10, github_token, logger)
        recent_commits_count = len(commits)
        if recent_commits_count > 0:
            print(f"   Found {recent_commits_count} recent commits")
        else:
            print("   ⚠️ No commits found")
        
        last_commit_date = "Unknown"
        if commits and commits[0].get("commit", {}).get("committer", {}).get("date"):
            last_commit_date = commits[0]["commit"]["committer"]["date"]
        
        # Prepare last commit message
        last_commit_message = "No commits available"
        if commits and commits[0].get("commit", {}).get("message"):
            last_commit_message = commits[0]["commit"]["message"]
        
        # Prepare activity summary
        activity_summary = f"{recent_commits_count} recent commits. Latest commit on {last_commit_date}: {last_commit_message[:50]}..."
        
        # Prepare repository data for analysis
        repo_data = {
            "name": repo_info["name"],
            "description": repo_info.get("description", "No description available"),
            "url": repo_info.get("html_url", ""),
            "updated_at": repo_info.get("updated_at", ""),
            "is_archived": repo_info.get("archived", False),
            "stars": repo_info.get("stargazers_count", 0),
            "forks": repo_info.get("forks_count", 0),
            "languages": language_breakdown or "No language information available",
            "open_issues": repo_info.get("open_issues_count", 0),
            "closed_issues": 0,  # Not directly available from the API
            "activity_summary": activity_summary,
            "recent_commits_count": recent_commits_count,
            "contributor_summary": f"Repository owned by {username}",
            "dependency_info": "Dependency information not available",
            "readme_content": readme_content or "No README content available",
        }
        
        # Create prompt for Claude
        prompt = format_analysis_prompt(repo_data)
        
        # Call Claude API
        print(f"🧠 Analyzing {repo_name} with Claude...")
        print(f"   Using model: {settings.llm_model}")
        if logger:
            logger.log(f"Analyzing {repo_name} with Claude model {settings.llm_model}")
        
        start_time = time.time()
        
        # Make API call
        try:
            response = call_claude_api(
                api_key=settings.anthropic_api_key,
                model_name=settings.llm_model,
                prompt=prompt,
                max_tokens=4000,
                logger=logger
            )
            
            elapsed_time = time.time() - start_time
            print(f"✅ API call completed in {elapsed_time:.2f} seconds")
            if logger:
                logger.log(f"API call completed in {elapsed_time:.2f} seconds")
        except Exception as e:
            print(f"\n❌ API call failed: {e}")
            print("   Please check your Anthropic API key and network connection")
            if logger:
                logger.log(f"API call failed: {e}", level="error")
            return
        
        # Extract and parse the response
        if not response or "content" not in response:
            if logger:
                logger.log("Error: No valid response from the API", level="error")
            print("❌ Error: No valid response from the API")
            print("   The API response did not contain expected content")
            return
            
        content = response.get("content", [])
        if not content or len(content) == 0:
            if logger:
                logger.log("Error: Empty content in API response", level="error")
            print("❌ Error: Empty content in API response")
            return
            
        text = content[0].get("text", "")
        if not text:
            if logger:
                logger.log("Error: No text in API response", level="error")
            print("❌ Error: No text in API response")
            return
        
        # Parse JSON from response
        print("🔍 Parsing analysis results...")
        
        # Check if the response is wrapped in markdown code block (```json ... ```)
        json_pattern = r"```json\s*({.*?})\s*```"
        json_match = re.search(json_pattern, text, re.DOTALL)
        
        if json_match:
            # Extract JSON from markdown code block
            clean_text = json_match.group(1)
            if logger:
                logger.log("Found JSON in markdown code block, extracting...", level="info")
            print("   Found JSON in markdown code block, extracting...")
        else:
            clean_text = text
        
        try:
            analysis = json.loads(clean_text)
            print("   ✅ Successfully parsed analysis data")
        except json.JSONDecodeError:
            # Try a more aggressive cleanup
            try:
                # If still fails, try to find any JSON-like structure with braces
                last_ditch_pattern = r"({[\s\S]*})"
                last_match = re.search(last_ditch_pattern, text)
                if last_match:
                    possible_json = last_match.group(1)
                    analysis = json.loads(possible_json)
                    print("   ✅ Successfully parsed analysis data (fallback method)")
                else:
                    raise ValueError("Could not find JSON structure in response")
            except Exception:
                if logger:
                    logger.log("Error: Failed to parse JSON from API response", level="error")
                    logger.log(f"Response text: {text[:200]}...", level="error")
                print("❌ Error: Failed to parse JSON from API response")
                print("   The response from Claude was not valid JSON")
                print(f"   Response preview: {text[:100]}...")
                return
        
        # Generate and write analysis report
        output_file = output_path / f"{repo_name}.md"
        print("📝 Generating analysis report...")
        print(f"   Output file: {output_file}")
        if logger:
            logger.log(f"Writing analysis to {output_file}")
        
        generate_analysis_report(
            output_file=output_file,
            repo_name=repo_name,
            repo_data=repo_data,
            analysis=analysis,
            language_breakdown=language_breakdown,
            recent_commits_count=recent_commits_count
        )
        
        print("\n✅ Analysis complete!")
        print(f"📊 Results written to: {output_file}")
        if 'recommended_action' in analysis:
            print(f"🔍 Recommended action: {analysis['recommended_action']}")
        print("\n💡 To view the report, open the file with a Markdown viewer or browser")
        
        if logger:
            logger.log(f"Analysis complete! Results written to {output_file}")
    
    except ValueError as e:
        if logger:
            logger.log(f"Error parsing repository input: {e}", level="error")
        print(f"❌ Error parsing repository input: {e}")
        print("   Please check the repository URL or owner/repo format")
    except Exception as e:
        if logger:
            logger.log(f"Error during analysis: {e}", level="error")
        print(f"❌ Error during analysis: {e}")
        print("   Please check the logs for details")
        import traceback
        traceback.print_exc()

def print_banner():
    """Print a banner with script information."""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                   GitHub Repo Analyzer                    ║
║                                                           ║
║  Analyze any GitHub repository by URL or owner/repo path  ║
╚═══════════════════════════════════════════════════════════╝
"""
    print(banner)

def main():
    """Main entry point for the script."""
    print_banner()
    
    # Setup argument parsing
    if len(sys.argv) < 2:
        print("Error: Missing repository input")
        print("\nUsage:")
        print("  poetry run analyze-repo <repo-url-or-path> [output_dir]")
        print("\nExamples:")
        print("  poetry run analyze-repo https://github.com/username/repo-name")
        print("  poetry run analyze-repo username/repo-name")
        print("  poetry run analyze-repo username/repo-name ./my-output-dir")
        sys.exit(1)
    
    repo_input = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '.out/repos'
    
    try:
        # Load settings
        print("\n🔧 Loading configuration...")
        try:
            settings = load_settings()
            if not settings.anthropic_api_key:
                print("⚠️ Warning: Anthropic API key not found in settings")
                print("   Analysis will fail without a valid API key")
            if not settings.github_token:
                print("⚠️ Warning: GitHub token not found in settings")
                print("   Rate limits will be restricted without a token")
        except Exception as e:
            print(f"❌ Error loading settings: {e}")
            print("   Falling back to default settings")
            settings = type('Settings', (), {
                'anthropic_api_key': os.environ.get('ANTHROPIC_API_KEY', ''),
                'github_token': os.environ.get('GITHUB_TOKEN', ''),
                'llm_model': 'claude-3-haiku-20240307',
                'debug_mode': False
            })
        
        github_token = settings.github_token
        
        # Setup logging
        print("📋 Setting up logging...")
        log_dir = Path(output_dir) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "analysis.log"
        logger = Logger(str(log_file), None, debug_enabled=settings.debug_mode if hasattr(settings, 'debug_mode') else False)
        
        # Print repository info
        try:
            owner, repo = parse_repository_input(repo_input)
            print(f"\n🔍 Analyzing repository: {owner}/{repo}")
            print(f"📁 Output directory: {Path(output_dir).absolute()}")
        except ValueError as e:
            print(f"\n❌ {e}")
            sys.exit(1)
        
        # Run analysis
        print("\n🚀 Starting analysis process...\n")
        analyze_repository(repo_input, github_token, output_dir, logger)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("   Please check the logs for details")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()