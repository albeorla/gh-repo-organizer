#!/usr/bin/env python3
"""GitHub Repository Analyzer
--------------------------
Analyzes GitHub repositories using Langchain and Anthropic Claude to generate insights,
recommendations, and documentation.
"""

import datetime
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import git
from dotenv import load_dotenv

# Langchain imports
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field

# Local utilities
from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn

# Load environment variables from .env file
load_dotenv()

# Initialize Rich console for pretty output
console = Console()

# Configuration from environment variables
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv(
    "GITHUB_USERNAME", "albeorla"
)  # Default to albeorla if not specified
OUTPUT_DIR = os.path.expanduser(os.getenv("OUTPUT_DIR", "~/dev/github/repo-info-docs"))
MAX_REPOS = int(os.getenv("MAX_REPOS", "100"))

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Setup logging
LOG_FILE = os.path.join(OUTPUT_DIR, "analysis_log.txt")


def log(message: str) -> None:
    """Log a message to both console and log file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    console.print(log_message)
    with open(LOG_FILE, "a") as logf:
        logf.write(log_message + "\n")


# Models for structured output
class LanguageBreakdown(BaseModel):
    """Breakdown of programming languages used in a repository."""

    language: str = Field(description="Programming language name")
    percentage: float = Field(description="Percentage of code in this language")


class RepoRecommendation(BaseModel):
    """Recommendations for a repository."""

    recommendation: str = Field(
        description="Specific recommendation for the repository"
    )
    reason: str = Field(description="Reason for the recommendation")
    priority: str = Field(description="Priority level (High, Medium, Low)")


class RepoAnalysis(BaseModel):
    """Comprehensive analysis of a GitHub repository."""

    repo_name: str = Field(description="Name of the repository")
    summary: str = Field(
        description="Brief summary of the repository's purpose and function"
    )
    strengths: list[str] = Field(description="Key strengths of the repository")
    weaknesses: list[str] = Field(description="Areas that could be improved")
    recommendations: list[RepoRecommendation] = Field(
        description="Specific recommendations"
    )
    activity_assessment: str = Field(
        description="Assessment of repository activity level"
    )
    estimated_value: str = Field(
        description="Estimated value/importance of the repository (High, Medium, Low)"
    )
    tags: list[str] = Field(description="Suggested tags/categories for the repository")


# Initialize Anthropic Claude model
def get_llm() -> ChatAnthropic:
    """Initialize and return the Anthropic Claude model."""
    if not ANTHROPIC_API_KEY:
        console.print(
            "[bold red]ERROR: ANTHROPIC_API_KEY not found in environment variables[/bold red]"
        )
        console.print(
            "Please create a .env file with your API key or set it in your environment"
        )
        sys.exit(1)

    return ChatAnthropic(
        model="claude-3-7-sonnet-latest",
        temperature=0.2,
        anthropic_api_key=ANTHROPIC_API_KEY,
    )


# GitHub CLI wrapper functions
def get_github_repos() -> list[dict[str, Any]]:
    """Fetch repository information using GitHub CLI."""
    log("Fetching repositories from GitHub...")

    try:
        result = subprocess.run(
            [
                "gh",
                "repo",
                "list",
                "--limit",
                str(MAX_REPOS),
                "--json",
                "name,description,url,updatedAt,isArchived,stargazerCount,forkCount",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            log(f"Error fetching repos: {result.stderr}")
            sys.exit(1)

        repos = json.loads(result.stdout)
        log(f"Successfully fetched {len(repos)} repositories")
        return repos
    except subprocess.TimeoutExpired:
        log("Timeout while fetching repository list")
        sys.exit(1)
    except Exception as e:
        log(f"Error fetching repository list: {str(e)}")
        sys.exit(1)


def get_repo_languages(repo_name: str) -> dict[str, float]:
    """Get the language breakdown for a repository."""
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{GITHUB_USERNAME}/{repo_name}/languages"],
            capture_output=True,
            text=True,
            timeout=15,
        )

        if result.returncode == 0 and result.stdout:
            languages = json.loads(result.stdout)
            if languages:
                # Convert bytes to percentages
                total = sum(languages.values())
                return {
                    lang: (value / total) * 100 for lang, value in languages.items()
                }

        return {}
    except Exception as e:
        log(f"Error fetching languages for {repo_name}: {str(e)}")
        return {}


def get_repo_commits(repo_path: str, limit: int = 10) -> list[dict[str, str]]:
    """Get recent commits for a repository."""
    try:
        if not os.path.isdir(repo_path):
            return []

        repo = git.Repo(repo_path)
        commits = []

        for commit in list(repo.iter_commits("HEAD", max_count=limit)):
            commits.append(
                {
                    "hash": commit.hexsha[:7],
                    "message": commit.message.split("\n")[0],
                    "author": commit.author.name,
                    "date": datetime.datetime.fromtimestamp(
                        commit.committed_date
                    ).strftime("%Y-%m-%d"),
                }
            )

        return commits
    except Exception as e:
        log(f"Error fetching commits for {repo_path}: {str(e)}")
        return []


def get_repo_contributors(repo_path: str) -> list[dict[str, Any]]:
    """Get contributors for a repository."""
    try:
        if not os.path.isdir(repo_path):
            return []

        repo = git.Repo(repo_path)
        result = subprocess.run(
            ["git", "shortlog", "-sn", "--no-merges"],
            capture_output=True,
            text=True,
            cwd=repo_path,
        )

        contributors = []
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if line.strip():
                    parts = line.strip().split("\t")
                    if len(parts) == 2:
                        count, name = parts
                        contributors.append(
                            {"name": name.strip(), "commits": int(count.strip())}
                        )

        return contributors
    except Exception as e:
        log(f"Error fetching contributors for {repo_path}: {str(e)}")
        return []


# Repository analysis with LLM
def analyze_repository(llm: ChatAnthropic, repo_info: dict[str, Any]) -> RepoAnalysis:
    """Analyze a repository using Claude to generate insights."""
    repo_name = repo_info.get("name", "")
    repo_desc = repo_info.get("description", "No description")
    repo_url = repo_info.get("url", "")
    updated_at = (
        repo_info.get("updatedAt", "").split("T")[0]
        if "updatedAt" in repo_info
        else "Unknown"
    )
    is_archived = repo_info.get("isArchived", False)
    stars = repo_info.get("stargazerCount", 0)
    forks = repo_info.get("forkCount", 0)

    # Get additional data
    languages = get_repo_languages(repo_name)
    lang_breakdown = [
        f"{lang}: {percentage:.1f}%"
        for lang, percentage in sorted(
            languages.items(), key=lambda x: x[1], reverse=True
        )
    ]

    local_repo_path = os.path.expanduser(f"~/dev/github/{repo_name}")
    commits = get_repo_commits(local_repo_path)
    recent_commits = (
        "\n".join(
            [
                f"- {commit['hash']} - {commit['message']} ({commit['date']}) <{commit['author']}>"
                for commit in commits
            ]
        )
        if commits
        else "No recent commits"
    )

    contributors = get_repo_contributors(local_repo_path)
    contributor_list = (
        "\n".join(
            [
                f"- {contributor['name']}: {contributor['commits']} commits"
                for contributor in contributors
            ]
        )
        if contributors
        else "No contributor data"
    )

    # Has local repo
    has_local = os.path.isdir(local_repo_path)

    # Create parser
    parser = PydanticOutputParser(pydantic_object=RepoAnalysis)

    # Prepare the analysis prompt
    repo_analysis_template = """
    You are an expert software developer and GitHub repository analyst. Your task is to analyze a GitHub repository 
    and provide insights, recommendations, and an assessment of its value.
    
    Here is the information about the repository:
    
    - Name: {repo_name}
    - Description: {repo_desc}
    - URL: {repo_url}
    - Last Updated: {updated_at}
    - Archived on GitHub: {is_archived}
    - Stars: {stars}
    - Forks: {forks}
    - Programming Languages: {languages}
    - Has Local Copy: {has_local}
    
    Recent Activity:
    {recent_commits}
    
    Contributors:
    {contributor_list}
    
    Based on the above information, provide a comprehensive analysis of this repository that includes:
    
    1. A brief summary of the repository's purpose and function
    2. Key strengths of the repository
    3. Areas that could be improved
    4. Specific recommendations with reasons and priority levels
    5. An assessment of the repository's activity level
    6. An estimated value/importance of the repository (High, Medium, Low)
    7. Suggested tags/categories for the repository
    
    {format_instructions}
    """

    # Set up the prompt
    prompt = PromptTemplate(
        template=repo_analysis_template,
        input_variables=[
            "repo_name",
            "repo_desc",
            "repo_url",
            "updated_at",
            "is_archived",
            "stars",
            "forks",
            "languages",
            "has_local",
            "recent_commits",
            "contributor_list",
        ],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    # Create the chain
    chain = LLMChain(llm=llm, prompt=prompt)

    # Run the chain
    log(f"Analyzing repository: {repo_name}...")

    try:
        result = chain.run(
            repo_name=repo_name,
            repo_desc=repo_desc,
            repo_url=repo_url,
            updated_at=updated_at,
            is_archived=is_archived,
            stars=stars,
            forks=forks,
            languages="\n".join(lang_breakdown)
            if lang_breakdown
            else "No language data",
            has_local=has_local,
            recent_commits=recent_commits,
            contributor_list=contributor_list,
        )

        # Parse the result
        analysis = parser.parse(result)
        log(f"Successfully analyzed repository: {repo_name}")
        return analysis
    except Exception as e:
        log(f"Error analyzing repository {repo_name}: {str(e)}")
        # Return a simple analysis with the error
        return RepoAnalysis(
            repo_name=repo_name,
            summary=f"Error analyzing repository: {str(e)}",
            strengths=[],
            weaknesses=["Could not be analyzed"],
            recommendations=[
                RepoRecommendation(
                    recommendation="Retry analysis",
                    reason="Analysis failed",
                    priority="Medium",
                )
            ],
            activity_assessment="Unknown",
            estimated_value="Unknown",
            tags=["error"],
        )


def generate_report(repos: list[dict[str, Any]], analyses: list[RepoAnalysis]) -> None:
    """Generate a comprehensive report of all repositories."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create main report
    main_report_path = os.path.join(OUTPUT_DIR, "repositories_report.md")
    log(f"Generating main report at {main_report_path}...")

    with open(main_report_path, "w") as f:
        f.write("# GitHub Repositories Analysis\n\n")
        f.write(f"Generated on {now}\n\n")
        f.write("## Summary\n\n")

        # Count repos by value
        high_value = sum(1 for a in analyses if "high" in a.estimated_value.lower())
        medium_value = sum(1 for a in analyses if "medium" in a.estimated_value.lower())
        low_value = sum(1 for a in analyses if "low" in a.estimated_value.lower())
        unknown_value = sum(
            1 for a in analyses if "unknown" in a.estimated_value.lower()
        )

        f.write(f"- Total repositories analyzed: {len(analyses)}\n")
        f.write(f"- High value repositories: {high_value}\n")
        f.write(f"- Medium value repositories: {medium_value}\n")
        f.write(f"- Low value repositories: {low_value}\n")
        f.write(f"- Unknown value repositories: {unknown_value}\n\n")

        # Create tables by value category
        f.write("## High Value Repositories\n\n")
        f.write("| Repository | Description | Activity | Tags |\n")
        f.write("|------------|-------------|----------|------|\n")
        for analysis in sorted(
            [a for a in analyses if "high" in a.estimated_value.lower()],
            key=lambda x: x.repo_name,
        ):
            tags = ", ".join(analysis.tags[:3]) if analysis.tags else ""
            f.write(
                f"| [{analysis.repo_name}]({analysis.repo_name}.md) | {analysis.summary[:100]}... | "
            )
            f.write(f"{analysis.activity_assessment} | {tags} |\n")

        f.write("\n## Medium Value Repositories\n\n")
        f.write("| Repository | Description | Activity | Tags |\n")
        f.write("|------------|-------------|----------|------|\n")
        for analysis in sorted(
            [a for a in analyses if "medium" in a.estimated_value.lower()],
            key=lambda x: x.repo_name,
        ):
            tags = ", ".join(analysis.tags[:3]) if analysis.tags else ""
            f.write(
                f"| [{analysis.repo_name}]({analysis.repo_name}.md) | {analysis.summary[:100]}... | "
            )
            f.write(f"{analysis.activity_assessment} | {tags} |\n")

        f.write("\n## Low Value Repositories\n\n")
        f.write("| Repository | Description | Activity | Tags |\n")
        f.write("|------------|-------------|----------|------|\n")
        for analysis in sorted(
            [a for a in analyses if "low" in a.estimated_value.lower()],
            key=lambda x: x.repo_name,
        ):
            tags = ", ".join(analysis.tags[:3]) if analysis.tags else ""
            f.write(
                f"| [{analysis.repo_name}]({analysis.repo_name}.md) | {analysis.summary[:100]}... | "
            )
            f.write(f"{analysis.activity_assessment} | {tags} |\n")

    # Generate individual repo markdown files
    for analysis in analyses:
        repo_name = analysis.repo_name
        repo_info = next((r for r in repos if r.get("name") == repo_name), {})

        repo_file_path = os.path.join(OUTPUT_DIR, f"{repo_name}.md")
        log(f"Generating report for {repo_name} at {repo_file_path}...")

        with open(repo_file_path, "w") as f:
            f.write(f"# {repo_name}\n\n")

            # Basic Information
            f.write("## Basic Information\n\n")
            f.write(
                f"- **URL**: [{repo_info.get('url', '')}]({repo_info.get('url', '')})\n"
            )
            f.write(
                f"- **Description**: {repo_info.get('description', 'No description')}\n"
            )
            f.write(
                f"- **Last Updated**: {repo_info.get('updatedAt', '').split('T')[0] if 'updatedAt' in repo_info else 'Unknown'}\n"
            )
            f.write(f"- **Archived**: {repo_info.get('isArchived', False)}\n")
            f.write(f"- **Stars**: {repo_info.get('stargazerCount', 0)}\n")
            f.write(f"- **Forks**: {repo_info.get('forkCount', 0)}\n\n")

            # Local Information
            f.write("## Local Information\n\n")
            local_repo_path = os.path.expanduser(f"~/dev/github/{repo_name}")
            if os.path.isdir(local_repo_path):
                # Get the size
                size_result = subprocess.run(
                    ["du", "-sh", local_repo_path], capture_output=True, text=True
                )
                size = (
                    size_result.stdout.strip().split("\t")[0]
                    if size_result.returncode == 0
                    else "Unknown"
                )

                f.write(f"- **Local Size**: {size}\n")
                f.write(
                    f"- **Local Path**: `/Users/aorlando/dev/github/{repo_name}`\n\n"
                )
            else:
                f.write("- **Local Repository**: Not found\n\n")

            # Analysis
            f.write("## Analysis Summary\n\n")
            f.write(f"{analysis.summary}\n\n")

            f.write("### Strengths\n\n")
            for strength in analysis.strengths:
                f.write(f"- {strength}\n")
            f.write("\n")

            f.write("### Areas for Improvement\n\n")
            for weakness in analysis.weaknesses:
                f.write(f"- {weakness}\n")
            f.write("\n")

            f.write("### Recommendations\n\n")
            for rec in analysis.recommendations:
                f.write(f"- **{rec.recommendation}** ({rec.priority} Priority)  \n")
                f.write(f"  *Reason: {rec.reason}*\n")
            f.write("\n")

            f.write("### Assessment\n\n")
            f.write(f"- **Activity Level**: {analysis.activity_assessment}\n")
            f.write(f"- **Estimated Value**: {analysis.estimated_value}\n")
            f.write(f"- **Tags**: {', '.join(analysis.tags)}\n\n")

            # Action Items
            f.write("## Action Items\n\n")
            f.write("- [ ] Review repository and confirm assessed value\n")
            f.write("- [ ] Implement high-priority recommendations\n")
            f.write("- [ ] Update documentation if keeping\n")
            if "low" in analysis.estimated_value.lower():
                f.write("- [ ] Consider archiving or deleting if no longer needed\n")


def main():
    """Main function to analyze repositories."""
    log("Starting GitHub repository analysis...")

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Clean up existing files
    log("Cleaning up existing files...")
    existing_files = list(Path(OUTPUT_DIR).glob("*.md"))
    log(f"Found {len(existing_files)} existing files to clean up")
    for file_path in existing_files:
        if file_path.name != "README.md":  # Preserve README if it exists
            try:
                os.remove(file_path)
                log(f"Removed {file_path.name}")
            except Exception as e:
                log(f"Error removing {file_path.name}: {str(e)}")

    # Initialize Anthropic Claude
    llm = get_llm()

    # Get repositories
    repos = get_github_repos()

    # Create analysis log
    log(f"Analyzing {len(repos)} repositories...")

    analyses = []

    # Process each repository
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Analyzing repositories...", total=len(repos))

        for repo in repos:
            repo_name = repo.get("name", "")
            progress.update(task, description=f"[cyan]Analyzing {repo_name}...")

            # Analyze the repository
            analysis = analyze_repository(llm, repo)
            analyses.append(analysis)

            progress.advance(task)

    # Generate final report
    generate_report(repos, analyses)

    log(f"Analysis complete. Reports generated in {OUTPUT_DIR}")
    log(f"Main report: {os.path.join(OUTPUT_DIR, 'repositories_report.md')}")


if __name__ == "__main__":
    main()
