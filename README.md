# GitHub Repository Organizer

A tool for analyzing and organizing GitHub repositories using AI-powered analysis with Domain-Driven Design architecture.

## Features

- Analyzes GitHub repositories to determine their purpose, value, and potential improvements
- Provides actionable decisions (DELETE/ARCHIVE/EXTRACT/KEEP/PIN) with reasoning
- Generates detailed markdown reports for each repository with strengths, weaknesses, and recommendations
- Creates summary reports categorizing repositories by value and activity level
- Supports both public and private repositories via GitHub token authentication
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

### Main Command

```bash
# The main command is 'repo'
poetry run repo --version              # Display version information
poetry run repo --help                 # Show help and command information
```

### Repository Management

```bash
# Analyze repositories
poetry run repo analyze                          # Analyze repositories for current user
poetry run repo analyze --owner <username>       # Analyze specific user's repositories
poetry run repo analyze --single-repo <name>  # Analyze a single repository by name
poetry run repo analyze --force --debug          # Force re-analysis with debug output
poetry run repo analyze --output-dir ~/reports   # Specify output directory

# Cleanup and maintenance
poetry run repo cleanup                          # Clean up analysis files
poetry run repo cleanup --force                  # Clean up without confirmation
poetry run repo reset                            # Reset analysis data that doesn't match your repositories
```

### Authentication for Private Repositories

To access private repositories, set up a GitHub personal access token:

1. Create a token at https://github.com/settings/tokens with `repo` scope
2. Set the token in your environment:

```bash
# Set environment variables
export GITHUB_TOKEN=your-github-token
export GITHUB_USERNAME=your-github-username

# Or create a .env file in the project root
echo "GITHUB_TOKEN=your-github-token" >> .env
echo "GITHUB_USERNAME=your-github-username" >> .env
```

With a valid token, the tool will automatically fetch both public and private repositories.

### Report Commands

```bash
# View reports 
poetry run repo reports                          # Show summary report
poetry run repo reports --repo <repository>      # Show specific repository report
poetry run repo reports --list                   # List all available repository reports
```

### Log Commands

```bash
# View logs
poetry run repo logs                             # Show latest log file
poetry run repo logs --all                       # List all available logs
poetry run repo logs --file <filename>           # View specific log file
```

### Action Commands

```bash
# Handle repository actions
poetry run repo actions --type all               # Execute all actions (dry run)
poetry run repo actions --type delete            # Execute only delete actions
poetry run repo actions --type archive           # Execute only archive actions
poetry run repo actions --force                  # Execute without confirmation
poetry run repo actions --no-dry-run             # Actually perform the operations
```

### Development Commands

```bash
# Development utilities
poetry run repo dev lint                         # Run linter
poetry run repo dev format                       # Format code
poetry run repo dev check                        # Run all checks
```

### Shell Completion

```bash
# Set up shell completion
poetry run repo completion install               # Install for detected shell
poetry run repo completion install --shell zsh   # Install for specific shell
poetry run repo completion bash                  # Output bash completion script
```

### Command Aliases and Options

The CLI features commonly used options across commands:

- `--force`, `-f`: Skip confirmation prompts
- `--debug`, `-d`: Enable debug logging
- `--quiet`, `-q`: Minimize console output
- `--output-dir`, `-o`: Specify custom output directory