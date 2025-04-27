# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Install dependencies: `poetry install`
- Run repo analyzer: `poetry run repo-analyzer analyze`
- Run with debug: `poetry run repo-analyzer analyze --debug`
- Force re-analysis: `poetry run repo-analyzer analyze --force`
- Clean up files: `poetry run repo-analyzer cleanup`
- Lint code: `poetry run ruff check .`
- Format code: `poetry run ruff format .`
- Run all tests: `poetry run pytest`
- Run specific test: `poetry run pytest tests/test_filename.py::TestClass::test_function`

## Code Style Guidelines
- **Python Version**: 3.12+
- **Line Length**: 88 characters (configured in pyproject.toml)
- **Typing**: Use type hints consistently (e.g., `list[str]`, `dict[str, Any]`)
- **Imports**: Group standard library first, then third-party, then local
- **Naming**: Classes in PascalCase, functions/methods in snake_case, constants in UPPER_SNAKE_CASE
- **Error Handling**: Use specific exceptions with appropriate try/except blocks
- **Documentation**: Google-style docstrings with clear descriptions
- **Testing**: Use unittest framework with mocks for external dependencies

## Architecture Overview
This project follows Domain-Driven Design (DDD) with hexagonal architecture:
- **Domain Layer**: Core business logic in `domain/` directory
- **Application Layer**: Use cases that orchestrate domain objects
- **Infrastructure Layer**: External integrations (GitHub API, LLM)
- **Interface Layer**: CLI commands and presentation logic

When contributing, ensure proper separation between layers and follow the DDD principles outlined in docs/guides/ddd-architecture.md.

## File Organization Strategy
- New domain models go in `domain/{bounded_context}/models.py`
- Domain interfaces in `domain/{bounded_context}/protocols.py`
- Domain services in `domain/{bounded_context}/services.py`
- Technical adapters in `infrastructure/{bounded_context}/{technology}_adapter.py`
- Use cases in `application/use_cases/`
- CLI commands in `cli/commands.py`