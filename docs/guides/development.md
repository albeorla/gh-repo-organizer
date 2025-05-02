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

## Development Workflow

### Running the Application

```bash
# Run the repository analyzer
poetry run repo-analyzer analyze

# Enable debug mode
poetry run repo-analyzer analyze --debug

# Force re-analysis of repositories
poetry run repo-analyzer analyze --force

# Analyze a single repository (useful for testing)
poetry run repo-analyzer analyze --single-repo my-repository-name

# Clean up report files
poetry run repo-analyzer cleanup
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

The project follows Domain-Driven Design principles with a hexagonal architecture. Here's the complete repository structure:

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

The key directories and their purposes:

- `src/repo_organizer/domain/` - Domain layer containing core business logic
  - `analysis/` - Analysis bounded context
  - `core/` - Core domain services and models
  - `source_control/` - Source control bounded context

- `src/repo_organizer/application/` - Application layer with use cases
  - Contains application services that orchestrate domain objects

- `src/repo_organizer/infrastructure/` - Infrastructure layer with external adapters
  - `analysis/` - Analysis adapters (LLM, etc.)
  - `source_control/` - GitHub API adapters
  - `config/` - Configuration management
  - `logging/` - Logging infrastructure
  - `rate_limiting/` - Rate limiting implementation

- `src/repo_organizer/cli/` - Interface layer (CLI)
  - Command-line interface implementation
  - Authentication middleware
  - Command handlers

- `src/repo_organizer/shared/` - Shared kernel
  - Common utilities and helpers
  - Shared types and interfaces

- `tests/` - Test suite organized by layer
  - Unit tests for each layer
  - Integration tests
  - Test fixtures and utilities

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