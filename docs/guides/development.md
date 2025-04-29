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

The project follows Domain-Driven Design principles with a hexagonal architecture:

```
src/repo_organizer/
├── domain/                # Domain layer
│   ├── analysis/          # Analysis bounded context
│   │   ├── models.py      # Domain models
│   │   ├── protocols.py   # Interfaces (ports)
│   │   └── services.py    # Domain services
│   └── source_control/    # Source control bounded context
├── application/           # Application layer
│   └── use_cases/         # Application services
├── infrastructure/        # Infrastructure layer
│   ├── analysis/          # Analysis adapters
│   └── source_control/    # Source control adapters
├── cli/                   # Interface layer (CLI)
└── shared/                # Shared kernel
```

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