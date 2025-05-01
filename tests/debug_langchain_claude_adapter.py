"""Debug script to trace the issue with LangChain Claude Adapter not passing repository data.

This script isolates the issue by tracking data flow through the adapter pipeline.
"""

import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from repo_organizer.infrastructure.analysis.langchain_claude_adapter import (
    LangChainClaudeAdapter,
)
from repo_organizer.utils.logger import Logger


class DebugLogger(Logger):
    """Enhanced logger for debugging that always outputs debug messages."""

    def __init__(self):
        self.debug_enabled = True
        self.logs = []

    def log(self, message, level="info"):
        """Log a message with specified level."""
        formatted = f"[{level.upper()}] {message}"
        print(formatted)
        self.logs.append((level, message))


def main():
    """Run the debug script to trace where repository data is lost."""
    # Load test data
    fixtures_path = Path(__file__).parent / "fixtures"
    with open(fixtures_path / "sample_repo_data.json") as f:
        sample_repo_data = json.load(f)

    # Create a debug logger that will capture all messages
    logger = DebugLogger()

    # Check if API key is available
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        return

    print("\n=== Testing LangChain Claude Adapter ===\n")

    # Create the adapter with debug logging
    adapter = LangChainClaudeAdapter(
        api_key=api_key,
        model_name="claude-3-7-sonnet-latest",
        temperature=0.2,
        thinking_enabled=True,
        thinking_budget=16000,
        logger=logger,
        enable_caching=False,  # Disable caching for testing
    )

    # Add additional fields to ensure we have a comprehensive dataset
    test_data = dict(sample_repo_data)
    test_data.update(
        {
            "open_issues": 5,
            "closed_issues": 10,
            "activity_summary": "Active development with 3 commits in the last month",
            "recent_commits_count": 3,
            "contributor_summary": "2 active contributors in the last 3 months",
            "dependency_info": "Requires requests, google-api-python-client",
        },
    )

    print("\n=== Repository Data Before Analysis ===\n")
    for key, value in test_data.items():
        print(f"{key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")

    print("\n=== Starting Analysis ===\n")

    try:
        # Perform the analysis
        result = adapter.analyze(test_data)

        print("\n=== Analysis Result ===\n")
        print(f"Repository: {result.repo_name}")
        print(f"Summary: {result.summary[:200]}...")
        print(f"Strengths: {result.strengths}")
        print(f"Weaknesses: {result.weaknesses}")
        print(f"Recommendations: {len(result.recommendations)} items")
        print(f"Activity: {result.activity_assessment}")
        print(f"Value: {result.estimated_value}")
        print(f"Tags: {result.tags}")
        print(f"Recommended Action: {result.recommended_action}")

        # Print adapter metrics for insight
        print("\n=== Adapter Metrics ===\n")
        metrics = adapter.get_metrics()
        for key, value in metrics.items():
            print(f"{key}: {value}")

    except Exception as e:
        print(f"\n=== ERROR: {e!s} ===\n")
        import traceback

        traceback.print_exc()

    print("\n=== Logger Messages Summary ===\n")
    print(f"Total log messages: {len(logger.logs)}")
    warning_logs = [msg for level, msg in logger.logs if level == "warning"]
    error_logs = [msg for level, msg in logger.logs if level == "error"]

    if warning_logs:
        print(f"\nWarnings ({len(warning_logs)}):")
        for msg in warning_logs:
            print(f"- {msg}")

    if error_logs:
        print(f"\nErrors ({len(error_logs)}):")
        for msg in error_logs:
            print(f"- {msg}")


if __name__ == "__main__":
    main()
