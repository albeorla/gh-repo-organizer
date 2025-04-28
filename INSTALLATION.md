# Installation Guide

This guide provides detailed instructions for setting up the GitHub Repository Organizer tool on your system.

## Prerequisites

- Python 3.12 or higher
- Poetry (package manager)
- GitHub account with Personal Access Token
- Anthropic API key for Claude AI

## Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/gh-repo-organizer.git
cd gh-repo-organizer
```

## Step 2: Install Dependencies

The project uses Poetry for dependency management:

```bash
# Install Poetry if you don't have it already
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

## Step 3: Configure Environment Variables

1. Create a `.env` file in the project root directory:

```bash
cp .env.example .env
```

2. Edit the `.env` file and add your API keys and configuration:

```
# Required API keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GITHUB_TOKEN=your_github_token_here
GITHUB_USERNAME=your_github_username
```

The minimal configuration requires:
- `ANTHROPIC_API_KEY`: Your Anthropic API key for Claude AI
- `GITHUB_TOKEN`: A GitHub Personal Access Token with repo access
- `GITHUB_USERNAME`: Your GitHub username

See [Configuration](README.md#configuration) for full list of environment variables.

## Step 4: Verify Installation

Run the following command to verify that everything is set up correctly:

```bash
poetry run repo-analyzer --version
```

You should see the version number of the tool.

## Step 5: Run the Tool

```bash
# Analyze your GitHub repositories
poetry run repo-analyzer analyze
```

For more usage examples, see the [README.md](README.md#usage) file.

## Troubleshooting

### Common Issues

1. **Poetry installation fails**
   - Ensure you have Python 3.12+ installed
   - Try using pip: `pip install poetry`

2. **Dependencies installation fails**
   - Make sure you have the latest version of Poetry: `poetry self update`
   - Try: `poetry install --no-cache`

3. **Authentication errors**
   - Verify your GITHUB_TOKEN has sufficient permissions
   - Ensure ANTHROPIC_API_KEY is valid and active
   - Check that your `.env` file is in the correct location

4. **Rate limiting issues**
   - Adjust rate limits in `.env` file:
     ```
     GITHUB_RATE_LIMIT=15  # Lower from default 30
     LLM_RATE_LIMIT=5      # Lower from default 10
     ```

### Getting Help

If you encounter issues not covered here:

1. Check the logs: `cat .logs/repo_organizer.log`
2. Enable debug mode: `poetry run repo-analyzer analyze --debug`
3. File an issue on the GitHub repository