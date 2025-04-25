# GitHub Repository Analyzer

A powerful tool that uses Langchain and Anthropic's Claude AI to analyze GitHub repositories, providing insights, recommendations, and documentation.

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your configuration:

   ```
   # API Keys
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   GITHUB_TOKEN=your_github_token_here  # If needed for higher API rate limits

   # GitHub Configuration
   GITHUB_USERNAME=albeorla

   # Repository Organizer Settings
   OUTPUT_DIR=~/dev/github/repo-info-docs
   MAX_REPOS=100
   ```

3. Run the analyzer:
   ```bash
   python repo_analyzer.py
   ```

## Output

The analyzer will generate detailed markdown files for each repository in the OUTPUT_DIR. These files include:

- Repository summary and purpose
- Strengths and weaknesses analysis
- Prioritized recommendations
- Activity assessment
- Value classification (High/Medium/Low)
- Tags/categories for organization

A main summary report will also be generated that categorizes repositories by value.

## Features

- Automatically analyzes all GitHub repositories for a user
- Generates detailed reports for each repository with:
  - Basic repository information
  - Local information (size, path)
  - Strengths and weaknesses analysis
  - Prioritized recommendations
  - Activity assessment
  - Value estimation
  - Tagged categories
  - Action items
- Creates a comprehensive summary report categorizing repositories by value
- Provides intelligent pruning recommendations

## Prerequisites

- Python 3.10+
- GitHub CLI (`gh`) installed and authenticated
- Anthropic API key

## Configuration

The following environment variables can be configured in your `.env` file:

- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
- `GITHUB_TOKEN`: GitHub token for API access (optional)
- `GITHUB_USERNAME`: Your GitHub username
- `OUTPUT_DIR`: Directory where reports will be generated
- `MAX_REPOS`: Maximum number of repositories to analyze

## Example Output

The analyzer generates detailed reports for each repository, including:

- Repository summary and purpose
- Technical strengths and weaknesses
- Prioritized improvement recommendations
- Activity level assessment
- Value classification (High/Medium/Low)
- Relevant tags and categories
- Recommended actions

## License

MIT
