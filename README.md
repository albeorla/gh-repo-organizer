# GitHub Repository Organizer

A tool for analyzing and organizing GitHub repositories using AI-powered analysis with Domain-Driven Design architecture.

## Features

- Analyzes GitHub repositories to determine their purpose, value, and potential improvements
- Provides actionable decisions (DELETE/ARCHIVE/EXTRACT/KEEP/PIN) with reasoning
- Generates detailed markdown reports for each repository with strengths, weaknesses, and recommendations
- Creates summary reports categorizing repositories by value and activity level
- Utilizes Domain-Driven Design (DDD) architecture for better reliability and maintainability
- Integrates with Claude AI for intelligent repository analysis
- Supports extended thinking for more thorough and accurate analyses
- Configurable LLM parameters including model selection and temperature
- Handles rate limiting and provides robust error recovery
- Modern command-line interface with rich console output and shell completion

## Installation

There are two ways to install the GitHub Repository Organizer:

### 1. Global Installation with pipx (Recommended)

```bash
# Install pipx if you haven't already
python -m pip install --user pipx
python -m pipx ensurepath

# Install gh-repo-organizer
pipx install gh-repo-organizer

# Enable shell completion (optional, but recommended)
repo completion install
```

### 2. Development Installation with Poetry

```bash
# Clone the repository
git clone https://github.com/yourusername/gh-repo-organizer.git
cd gh-repo-organizer

# Install dependencies
poetry install

# Enable shell completion (optional, but recommended)
poetry run repo completion install
```

## Usage

The CLI provides a set of intuitive command groups for managing GitHub repositories:

### Repository Management (`repo`)

```bash
# Analyze repositories
repo repo analyze                     # Analyze your repositories
repo repo analyze --owner <username>  # Analyze specific user's repos
repo repo analyze --single <name>     # Analyze a single repository

# Cleanup and maintenance
repo repo cleanup                     # Clean up analysis files
repo repo reset                       # Reset all analysis data
```

### Report Management (`reports`)

```bash
# View and manage reports
repo reports list                     # List available reports
repo reports show <repository>        # Show specific report
repo reports summary                  # Show analysis summary
```

### Log Management (`logs`)

```bash
# Access and view logs
repo logs latest                      # Show latest log file
repo logs all                        # List all log files
repo logs view <file>                # View specific log file
```

### Action Management (`actions`)

```bash
# Handle repository actions
repo actions list                     # List pending actions
repo actions execute                  # Execute pending actions
repo actions dry-run                  # Simulate action execution
```

### Command Aliases

For convenience, you can use the shorter alias `ro` instead of `repo`:

```bash
ro repo analyze      # Same as 'repo repo analyze'
ro reports list     # Same as 'repo reports list'
ro logs latest      # Same as 'repo logs latest'
```

### Shell Completion

The CLI supports shell completion for all commands and options:

```bash
# Install shell completion (auto-detects shell)
repo completion install

# Or install for a specific shell
repo completion install --shell bash  # For Bash
repo completion install --shell zsh   # For Zsh
repo completion install --shell fish  # For Fish

# Remove shell completion
repo completion uninstall
```

### Repository Analysis Options

The `repo analyze` command supports these options:

- `--owner`, `-o`: GitHub owner/user to analyze (defaults to GITHUB_USERNAME)
- `--limit`, `-l`: Maximum number of repositories to analyze
- `--single`, `-s`: Analyze only the specified repository name
- `--output-dir`, `-d`: Directory for output files
- `--force`, `-f`: Force re-analysis of all repositories
- `--debug`: Enable debug logging
- `--quiet`, `-q`: Minimize console output

## Configuration

The tool can be configured via environment variables:

### Required Settings
- `GITHUB_USERNAME`: Your GitHub username
- `GITHUB_TOKEN`: GitHub Personal Access Token
- `ANTHROPIC_API_KEY`: API key for Claude AI

### LLM Settings
- `LLM_MODEL`: Claude model to use (default: "claude-3-7-sonnet-latest")
- `LLM_TEMPERATURE`: Temperature for LLM (0.0-1.0, default: 0.2)
- `LLM_THINKING_ENABLED`: Enable extended thinking ("true"/"false", default: "true")
- `LLM_THINKING_BUDGET`: Token budget for thinking (default: 16000)

### Advanced Configuration
- `OUTPUT_DIR`: Directory for output files (default: ".out/repos")
- `LOGS_DIR`: Directory for log files (default: ".logs")
- `MAX_REPOS`: Maximum number of repositories to analyze (default: 100)
- `MAX_WORKERS`: Number of parallel workers (default: 5)
- `GITHUB_RATE_LIMIT`: GitHub API calls per minute (default: 30)
- `LLM_RATE_LIMIT`: LLM API calls per minute (default: 10)
- `DEBUG_LOGGING`: Enable debug logging ("true"/"false", default: "false")
- `QUIET_MODE`: Minimize console output ("true"/"false", default: "false")

## Example Output

For each repository, the tool generates a detailed analysis like this:

```markdown
# youtube_playlist_organizer

## Basic Information

- **URL**: [https://github.com/username/youtube_playlist_organizer](https://github.com/username/youtube_playlist_organizer)
- **Description**: A tool for organizing and managing YouTube playlists
- **Last Updated**: 2025-04-06
- **Archived**: False
- **Stars**: 12
- **Forks**: 3

## Analysis Summary

This repository contains a tool for organizing and managing YouTube playlists. It provides functionality to combine playlists, remove duplicate videos, sort videos by various criteria, export playlist data, and create smart playlists based on specific criteria.

### Strengths

- Provides a comprehensive set of playlist management features
- Well-documented with clear installation and usage instructions
- Implements both command-line and programmatic interfaces

### Areas for Improvement

- Limited community engagement based on the relatively low number of stars and forks
- No mention of testing infrastructure or test coverage

### Recommendations

- **Add comprehensive test suite** (High Priority)  
  *Reason: Ensuring reliability and preventing regressions is critical*
- **Implement GitHub Actions for CI/CD** (Medium Priority)  
  *Reason: Automating testing and deployment would improve code quality*

### Assessment

- **Activity Level**: Moderate
- **Estimated Value**: Medium
- **Tags**: youtube-api, playlist-management, python, data-organization
```

## Development

```bash
# Run tests
poetry run pytest

# Format code
poetry run ruff format .

# Lint code
poetry run ruff check .

# Or use the dev commands
poetry run repo dev lint
poetry run repo dev format
poetry run repo dev check
```

## Single Repository Mode

The tool supports analyzing a single repository instead of the complete set of repositories owned by a user. This feature is useful for:

- **Testing and Debugging**: Focus on a specific repository to test changes or debug issues
- **Targeted Analysis**: Get detailed analysis for a repository of interest
- **Performance**: Significantly faster when you only need information about one repository
- **CI/CD Integration**: Use in continuous integration pipelines to analyze specific repositories

### Usage

```bash
# Analyze a single repository by name
repo repo analyze --single repository-name

# Combine with other options
repo repo analyze --single repository-name --force --debug
```

### Considerations

- The summary report will indicate it contains data for only one repository
- All analysis features work the same as in multi-repository mode
- Repository name must match exactly (case-sensitive)
- If the specified repository doesn't exist, an error will be shown

## Architecture

This project follows Domain-Driven Design (DDD) principles with a hexagonal architecture:

- **Domain Layer**: Core business logic and domain models
- **Application Layer**: Use cases that orchestrate domain objects
- **Infrastructure Layer**: External integrations (GitHub API, LLM)
- **Interface Layer**: CLI commands and presentation logic

For more details on the architecture and design decisions:

- See [CLAUDE.md](CLAUDE.md) for design principles and implementation patterns
- Check [docs/roadmap.md](docs/roadmap.md) for prioritized development tasks
- Review Architecture Decision Records in [docs/adr](docs/adr)
- Explore the full [documentation](docs/README.md)

## License

MIT License