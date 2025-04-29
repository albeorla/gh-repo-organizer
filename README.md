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
- Modern command-line interface with rich console output

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/gh-repo-organizer.git
cd gh-repo-organizer

# Install dependencies
poetry install
```

## Usage

```bash
# Analyze your GitHub repositories
poetry run repo-analyzer analyze

# Analyze repositories with specific options
poetry run repo-analyzer analyze --owner <username> --limit 10

# Analyze a single repository
poetry run repo-analyzer analyze --single-repo my-repository-name

# Force re-analysis of repositories
poetry run repo-analyzer analyze --force

# Enable debug mode for verbose logging
poetry run repo-analyzer analyze --debug

# Specify output directory
poetry run repo-analyzer analyze --output-dir ./my-reports

# Clean up report files
poetry run repo-analyzer cleanup

# View generated reports
poetry run repo-analyzer reports

# View analysis logs
poetry run repo-analyzer logs

# Reset and clean up analysis files
poetry run repo-analyzer reset
```

### Command-line Options

The `analyze` command supports the following options:

- `--owner`, `-o`: GitHub owner/user to analyze (defaults to GITHUB_USERNAME)
- `--limit`, `-l`: Maximum number of repositories to analyze
- `--single-repo`: Analyze only the specified repository name
- `--output-dir`: Directory for output files
- `--force`, `-f`: Force re-analysis of all repositories
- `--debug`, `-d`: Enable debug logging
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
poetry run repo-analyzer analyze --single-repo repository-name

# Combine with other options
poetry run repo-analyzer analyze --single-repo repository-name --force --debug
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