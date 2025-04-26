# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Install dependencies: `poetry install`
- Run the repo analyzer: `poetry run repo-analyzer analyze`
- Run with debugging: `poetry run repo-analyzer analyze --debug`
- Force re-analysis: `poetry run repo-analyzer analyze --force`
- Clean up report files: `poetry run repo-analyzer cleanup`
- Lint code: `poetry run ruff check .`
- Format code: `poetry run ruff format .`

## Code Style Guidelines
- **Python Version**: 3.12+
- **Formatting**: Line length 88 (configured in pyproject.toml)
- **Typing**: Use type hints consistently (e.g., `list[str]`, `dict[str, Any]`)
- **Imports**: Group standard library first, then third-party, then local
- **Naming**: 
  - Classes: PascalCase
  - Functions/methods: snake_case
  - Constants: UPPER_SNAKE_CASE
- **Error Handling**: Use appropriate try/except blocks with specific exceptions
- **Documentation**: Use docstrings with Google-style format

## Software Design Principles
- **Architecture**: Domain-Driven Design (DDD) with clear bounded contexts
- **SOLID Principles**:
  - Single Responsibility: Each class has one reason to change
  - Open/Closed: Open for extension, closed for modification
  - Liskov Substitution: Subtypes must be substitutable for base types
  - Interface Segregation: Use Protocol classes for narrow interfaces
  - Dependency Inversion: Depend on abstractions, not implementations
- **Design Patterns**:
  - Façade: ApplicationRunner simplifies complex subsystem interfaces
  - Strategy: LLMService implements various LLM backend strategies
  - Repository: GitHubService and Settings implement repository patterns
  - Factory: ApplicationFactory creates configured application instances
  - Command: ApplicationRunner.run() encapsulates analysis execution
  - Observer: ProgressReporter for progress updates to multiple clients
- **Package Structure**:
  - Hexagonal Architecture with domain models, services, and utils
  - Small files under 300 lines of code
  - Domain logic separate from infrastructure
  - Modern CLI with Typer and rich console output