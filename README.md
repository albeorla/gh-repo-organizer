# GitHub Repository Organizer

A tool for analyzing and organizing GitHub repositories using AI-powered analysis.

## Features

- Analyzes GitHub repositories to determine their purpose, value, and potential improvements
- Generates detailed markdown reports for each repository
- Creates summary reports categorizing repositories by value
- Integrates with Claude AI for intelligent repository analysis
- Handles rate limiting and error recovery

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

# Force re-analysis of repositories
poetry run repo-analyzer analyze --force

# Enable debug mode for verbose logging
poetry run repo-analyzer analyze --debug

# Clean up report files
poetry run repo-analyzer cleanup
```

## Configuration

The tool can be configured via environment variables:

- `GITHUB_USERNAME`: Your GitHub username
- `GITHUB_TOKEN`: GitHub Personal Access Token
- `ANTHROPIC_API_KEY`: API key for Claude AI

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

## License

MIT License