# GitHub Repository Analyzer

A powerful tool that uses Langchain and Anthropic's Claude AI to analyze GitHub repositories, providing insights, recommendations, and documentation.

## Setup

1. Install dependencies using Poetry:

   ```bash
   poetry install
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
   
   # Concurrency and Rate Limiting Settings
   MAX_WORKERS=5          # Number of parallel workers
   GITHUB_RATE_LIMIT=30   # GitHub API calls per minute
   LLM_RATE_LIMIT=10      # LLM API calls per minute
   ```

3. Run the analyzer:
   ```bash
   poetry run repo-analyzer analyze
   ```
   
   Or with additional options:
   ```bash
   # Show all available commands
   poetry run repo-analyzer --help
   
   # Force re-analysis of all repositories
   poetry run repo-analyzer analyze --force
   
   # Enable debug logging
   poetry run repo-analyzer analyze --debug
   
   # Specify output directory
   poetry run repo-analyzer analyze --output-dir ~/my-reports
   
   # Limit number of repositories
   poetry run repo-analyzer analyze --max-repos 20
   
   # Clean up analysis files
   poetry run repo-analyzer cleanup
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
- Parallel processing with customizable number of workers for faster analysis
- Smart rate limiting for GitHub and LLM API calls to prevent throttling
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

- Python 3.12+
- Poetry (https://python-poetry.org/docs/#installation)
- GitHub CLI (`gh`) installed and authenticated
- Anthropic API key

## Configuration

The following environment variables can be configured in your `.env` file:

- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
- `GITHUB_TOKEN`: GitHub token for API access (optional)
- `GITHUB_USERNAME`: Your GitHub username
- `OUTPUT_DIR`: Directory where reports will be generated
- `MAX_REPOS`: Maximum number of repositories to analyze
- `MAX_WORKERS`: Number of parallel workers for concurrent analysis (default: 5)
- `GITHUB_RATE_LIMIT`: Maximum GitHub API calls per minute (default: 30)
- `LLM_RATE_LIMIT`: Maximum LLM API calls per minute (default: 10)

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
