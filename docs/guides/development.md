# Development Guide

This guide provides information for developers contributing to the GitHub Repository Organizer.

## Development Environment Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/gh-repo-organizer.git
   cd gh-repo-organizer
   ```

2. **Install Poetry**
   ```bash
   # If you don't have Poetry installed
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies**
   ```bash
   poetry install
   ```

4. **Create environment file**
   Copy the `.env.example` file to `.env` and populate it with your API keys and configuration.
   ```bash
   cp .env.example .env
   # Edit .env with your favorite editor
   ```

5. **Enable shell completion (optional)**
   ```bash
   # Install shell completion for development
   poetry run repo completion install
   ```

## Development Workflow

### Running the Application

The CLI is organized into logical command groups. Here are common development workflows:

```bash
# Repository Analysis
poetry run repo repo analyze                     # Analyze your repositories
poetry run repo repo analyze --debug             # Enable debug mode
poetry run repo repo analyze --force             # Force re-analysis
poetry run repo repo analyze --single my-repo    # Analyze single repository
poetry run repo repo cleanup                     # Clean up reports

# Report Management
poetry run repo reports list                     # List reports
poetry run repo reports show my-repo             # View specific report
poetry run repo reports summary                  # View summary

# Log Management
poetry run repo logs latest                      # View latest log
poetry run repo logs all                         # List all logs
poetry run repo logs view my-log.txt            # View specific log

# Action Management
poetry run repo actions list                     # List pending actions
poetry run repo actions dry-run                  # Simulate actions
poetry run repo actions execute                  # Execute actions
```

For convenience, you can also use the shorter alias `ro`:

```bash
poetry run ro repo analyze --debug
poetry run ro reports list
poetry run ro logs latest
```

### Code Quality Tools

```bash
# Format code with ruff
poetry run ruff format .

# Lint code with ruff
poetry run ruff check .

# Run tests
poetry run pytest
```

## Code Organization

The project follows Domain-Driven Design principles with a hexagonal architecture. Here's the key directory structure:

```text
.
├── src
│   └── repo_organizer
│       ├── cli
│       │   ├── __init__.py
│       │   ├── app.py                # Main CLI application
│       │   ├── commands/             # Command group implementations
│       │   │   ├── __init__.py
│       │   │   ├── actions.py        # Action management commands
│       │   │   ├── logs.py          # Log management commands
│       │   │   ├── repo.py          # Repository management commands
│       │   │   └── reports.py       # Report management commands
│       │   └── auth_middleware.py    # Authentication middleware
│       ├── application
│       │   ├── __init__.py
│       │   └── analyze_repositories.py
│       ├── bootstrap
│       │   ├── __init__.py
│       │   ├── application_factory.py
│       │   └── application_runner.py
│       ├── config
│       │   └── __init__.py
│       ├── domain
│       │   ├── __init__.py
│       │   ├── analysis
│       │   │   ├── __init__.py
│       │   │   ├── action_recommendation_service.py
│       │   │   ├── events.py
│       │   │   ├── models.py
│       │   │   ├── protocols.py
│       │   │   ├── repository_analyzer_service.py
│       │   │   ├── services.py
│       │   │   └── value_objects.py
│       │   ├── core
│       │   │   ├── __init__.py
│       │   │   ├── auth_config.py
│       │   │   ├── auth_service.py
│       │   │   ├── auth_validator.py
│       │   │   └── events.py
│       │   └── source_control
│       │       ├── __init__.py
│       │       ├── models.py
│       │       └── protocols.py
│       ├── infrastructure
│       │   ├── __init__.py
│       │   ├── analysis
│       │   │   ├── __init__.py
│       │   │   ├── langchain_claude_adapter.py
│       │   │   ├── llm_service.py
│       │   │   └── pydantic_models.py
│       │   ├── config
│       │   │   ├── __init__.py
│       │   │   ├── auth_settings.py
│       │   │   └── settings.py
│       │   ├── documentation
│       │   ├── errors
│       │   │   ├── __init__.py
│       │   │   ├── error_handler.py
│       │   │   └── exceptions.py
│       │   ├── github_rest.py
│       │   ├── logging
│       │   │   ├── __init__.py
│       │   │   ├── auth_logger.py
│       │   │   └── logger.py
│       │   ├── rate_limiting
│       │   │   ├── __init__.py
│       │   │   ├── rate_limiter.py
│       │   │   └── retry.py
│       │   └── source_control
│       │       ├── __init__.py
│       │       ├── github_adapter.py
│       │       └── github_service.py
│       ├── interface
│       │   ├── __init__.py
│       │   └── cli
│       │       └── __init__.py
│       ├── models
│       ├── services
│       │   ├── __init__.py
│       │   ├── progress_reporter.py
│       │   └── service_interfaces.py
│       ├── shared
│       │   └── __init__.py
│       └── utils
│           ├── __init__.py
│           ├── exceptions.py
│           ├── logger.py
│           └── rate_limiter.py
└── tests
    ├── __init__.py
    ├── app
    ├── application
    │   └── test_single_repo_mode.py
    ├── cli
    │   ├── __init__.py
    │   ├── test_auth_middleware.py
    │   ├── test_commands.py
    │   └── test_execute_actions.py
    ├── conftest.py
    ├── debug_langchain_claude_adapter.py
    ├── domain
    │   ├── analysis
    │   │   ├── __init__.py
    │   │   ├── test_action_recommendation_service.py
    │   │   └── test_events.py
    │   └── core
    │       ├── __init__.py
    │       ├── test_auth_config.py
    │       ├── test_auth_service.py
    │       ├── test_auth_validator.py
    │       └── test_events.py
    ├── fixtures
    │   ├── expected_analysis_output.md
    │   ├── langchain_claude_adapter_fix.md
    │   └── sample_repo_data.json
    ├── infrastructure
    │   ├── __init__.py
    │   ├── analysis
    │   │   ├── __init__.py
    │   │   └── test_langchain_claude_adapter.py
    │   ├── config
    │   │   ├── __init__.py
    │   │   └── test_auth_settings.py
    │   └── source_control
    │       ├── __init__.py
    │       └── test_github_adapter.py
    ├── integration
    ├── services
    ├── test_analysis.py
    └── test_application.py
```

## CLI Development

### Command Group Structure

The CLI uses Typer's command groups pattern. Each command group is defined in its own module under `cli/commands/`:

```python
# src/repo_organizer/cli/commands/repo.py
import typer
from typing import Optional

repo_app = typer.Typer(
    name="repo",
    help="Repository management commands",
    short_help="Manage repositories"
)

@repo_app.command()
def analyze(
    owner: Optional[str] = typer.Option(None, "--owner", "-o", help="GitHub owner/user"),
    single: Optional[str] = typer.Option(None, "--single", "-s", help="Single repository"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
):
    """Analyze GitHub repositories."""
    # Command implementation
```

### Adding New Commands

To add a new command:

1. Choose the appropriate command group module (or create a new one)
2. Define your command using the `@app.command()` decorator
3. Add type hints and Typer options for parameters
4. Implement the command logic
5. Register the command group in `cli/app.py`

Example:

```python
# src/repo_organizer/cli/commands/reports.py
@reports_app.command()
def export(
    format: str = typer.Option("markdown", "--format", "-f", help="Export format"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Export reports in different formats."""
    # Implementation
```

### Testing Commands

Create tests in `tests/cli/commands/`:

```python
# tests/cli/commands/test_repo.py
from typer.testing import CliRunner
from repo_organizer.cli.app import app

runner = CliRunner()

def test_analyze_command():
    result = runner.invoke(app, ["repo", "analyze"])
    assert result.exit_code == 0
    # Add assertions for expected output
```

### Shell Completion

The CLI automatically supports shell completion through Typer. To test completion:

```bash
# Install completion in development
poetry run repo completion install

# Test completion
poetry run repo [TAB][TAB]
poetry run repo repo [TAB][TAB]
poetry run repo reports [TAB][TAB]
```

## Error Handling

Commands should use the error handling utilities in `infrastructure/errors/`:

```python
from repo_organizer.infrastructure.errors import handle_error

@repo_app.command()
def analyze(...):
    try:
        # Command logic
    except Exception as e:
        handle_error(e)
        raise typer.Exit(1)
```

## Documentation

When adding or modifying commands:

1. Update the command's docstring with clear usage information
2. Add examples in the help text using Typer's rich text formatting
3. Update the [CLI Migration Guide](cli-migration.md) if breaking changes are made
4. Update the main README.md with new command examples

## Environment Variables

Commands can access configuration through environment variables:

```python
from repo_organizer.infrastructure.config import settings

@repo_app.command()
def analyze(...):
    debug = settings.debug_logging
    # Use configuration
```

See the [Configuration Guide](configuration.md) for available settings.

## Implementation Patterns

### Composition over Inheritance

Prefer composition over inheritance for adapter implementations. For example:

```python
# Good: Composition-based adapter
class LangChainClaudeAdapter(AnalyzerPort):
    def __init__(self, api_key: str, ...):
        self._llm_service = LLMService(api_key=api_key, ...)
        
    def analyze(self, repo_data: Mapping[str, Any]) -> RepoAnalysis:
        # Use self._llm_service here
        
# Avoid: Inheritance-based adapter
class LangChainClaudeAdapter(LLMService, AnalyzerPort):
    def analyze(self, repo_data: Mapping[str, Any]) -> RepoAnalysis:
        # Mixing different responsibilities
```

### Backward Compatibility

When refactoring, maintain backward compatibility through:

1. Re-export of moved models through the original module path
2. Adapter classes that expose the old interface but use the new implementation
3. Deprecation notices in docstrings for future migration

### Progressive Enhancement

Implement changes incrementally, following the prioritization in `docs/roadmap.md`:

1. Focus on core domain models first
2. Then refactor infrastructure implementations
3. Finally, update CLI/interface components

### Testing Strategy

- Unit test core domain logic independently
- Use mocks for infrastructure dependencies
- Add integration tests for complete use cases
- Update tests as you refactor code

## Architecture Decision Records

Significant architectural decisions are documented in Architecture Decision Records (ADRs) located in `docs/adr/`. When making substantial changes:

1. Check if an existing ADR covers the decision area
2. If not, create a new ADR following the template in `docs/adr/README.md`

## Pull Request Process

1. Create a feature branch from `main`
2. Implement your changes following the guidelines in this document
3. Ensure all tests pass and code quality checks pass
4. Update documentation as needed
5. Create a pull request with a clear description of the changes
6. Address any review comments

## Repository Structure

```text
.
├── CLAUDE.md
├── README.md
├── docs
│   ├── CLAUDE.ARCHIVED.md
│   ├── README.md
│   ├── adr
│   │   ├── 0001-ddd-architecture.md
│   │   ├── 0002-repository-action-decisions.md
│   │   └── README.md
│   ├── auth_configuration.md
│   ├── guides
│   │   ├── ddd-architecture.md
│   │   └── development.md
│   ├── roadmap.txt
│   └── task-master-cli-help.md
├── pyproject.toml
├── scripts
│   ├── example_prd.txt
│   ├── prd.txt
│   └── task-complexity-report.json
├── src
│   └── repo_organizer
│       ├── __init__.py
│       ├── application
│       │   ├── __init__.py
│       │   └── analyze_repositories.py
│       ├── bootstrap
│       │   ├── __init__.py
│       │   ├── application_factory.py
│       │   └── application_runner.py
│       ├── cli
│       │   ├── __init__.py
│       │   ├── app.py
│       │   ├── auth_middleware.py
│       │   ├── commands.py
│       │   └── dev.py
│       ├── config
│       │   └── __init__.py
│       ├── domain
│       │   ├── __init__.py
│       │   ├── analysis
│       │   │   ├── __init__.py
│       │   │   ├── action_recommendation_service.py
│       │   │   ├── events.py
│       │   │   ├── models.py
│       │   │   ├── protocols.py
│       │   │   ├── repository_analyzer_service.py
│       │   │   ├── services.py
│       │   │   └── value_objects.py
│       │   ├── core
│       │   │   ├── __init__.py
│       │   │   ├── auth_config.py
│       │   │   ├── auth_service.py
│       │   │   ├── auth_validator.py
│       │   │   └── events.py
│       │   └── source_control
│       │       ├── __init__.py
│       │       ├── models.py
│       │       └── protocols.py
│       ├── infrastructure
│       │   ├── __init__.py
│       │   ├── analysis
│       │   │   ├── __init__.py
│       │   │   ├── langchain_claude_adapter.py
│       │   │   ├── llm_service.py
│       │   │   └── pydantic_models.py
│       │   ├── config
│       │   │   ├── __init__.py
│       │   │   ├── auth_settings.py
│       │   │   └── settings.py
│       │   ├── documentation
│       │   ├── errors
│       │   │   ├── __init__.py
│       │   │   ├── error_handler.py
│       │   │   └── exceptions.py
│       │   ├── github_rest.py
│       │   ├── logging
│       │   │   ├── __init__.py
│       │   │   ├── auth_logger.py
│       │   │   └── logger.py
│       │   ├── rate_limiting
│       │   │   ├── __init__.py
│       │   │   ├── rate_limiter.py
│       │   │   └── retry.py
│       │   └── source_control
│       │       ├── __init__.py
│       │       ├── github_adapter.py
│       │       └── github_service.py
│       ├── interface
│       │   ├── __init__.py
│       │   └── cli
│       │       └── __init__.py
│       ├── models
│       ├── services
│       │   ├── __init__.py
│       │   ├── progress_reporter.py
│       │   └── service_interfaces.py
│       ├── shared
│       │   └── __init__.py
│       └── utils
│           ├── __init__.py
│           ├── exceptions.py
│           ├── logger.py
│           └── rate_limiter.py
└── tests
    ├── __init__.py
    ├── app
    ├── application
    │   └── test_single_repo_mode.py
    ├── cli
    │   ├── __init__.py
    │   ├── test_auth_middleware.py
    │   ├── test_commands.py
    │   └── test_execute_actions.py
    ├── conftest.py
    ├── debug_langchain_claude_adapter.py
    ├── domain
    │   ├── analysis
    │   │   ├── __init__.py
    │   │   ├── test_action_recommendation_service.py
    │   │   └── test_events.py
    │   └── core
    │       ├── __init__.py
    │       ├── test_auth_config.py
    │       ├── test_auth_service.py
    │       ├── test_auth_validator.py
    │       └── test_events.py
    ├── fixtures
    │   ├── expected_analysis_output.md
    │   ├── langchain_claude_adapter_fix.md
    │   └── sample_repo_data.json
    ├── infrastructure
    │   ├── __init__.py
    │   ├── analysis
    │   │   ├── __init__.py
    │   │   └── test_langchain_claude_adapter.py
    │   ├── config
    │   │   ├── __init__.py
    │   │   └── test_auth_settings.py
    │   └── source_control
    │       ├── __init__.py
    │       └── test_github_adapter.py
    ├── integration
    ├── services
    ├── test_analysis.py
    └── test_application.py
```

## Environment Variables

The following environment variables are used to configure the application:

### API Keys
- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
- `GITHUB_TOKEN`: GitHub token for API access (optional)

### GitHub Configuration
- `GITHUB_USERNAME`: GitHub username (required)

### Repository Settings
- `OUTPUT_DIR`: Directory for output files (default: `.out/repos`)
- `LOGS_DIR`: Directory for log files (default: `.logs`)
- `MAX_REPOS`: Maximum number of repositories to analyze (default: 100)

### LLM Settings
- `LLM_MODEL`: LLM model to use (default: `claude-3-7-sonnet-latest`)
- `LLM_TEMPERATURE`: LLM temperature (0.0-1.0) (default: 0.2)
- `LLM_THINKING_ENABLED`: Enable extended thinking for LLM (default: true)
- `LLM_THINKING_BUDGET`: Token budget for LLM thinking (default: 16000)

### Concurrency and Rate Limiting
- `MAX_WORKERS`: Number of parallel workers (default: 5)
- `GITHUB_RATE_LIMIT`: GitHub API calls per minute (default: 30)
- `LLM_RATE_LIMIT`: LLM API calls per minute (default: 10)

### Debug Settings
- `DEBUG_LOGGING`: Enable debug logging (default: false)
- `QUIET_MODE`: Minimize console output (default: false)