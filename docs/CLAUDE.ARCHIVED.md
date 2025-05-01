# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Meta Instructions

### Planning Strategy

When working on this codebase, follow these planning steps:

1. **Understand the Request**
   - Identify if it's a feature addition, bug fix, refactoring, or other task
   - Map the request to the DDD bounded contexts (analysis, source_control)
   - Check ROADMAP.md to see if the task is already prioritized

2. **File Location Strategy**
   - New domain models go in `domain/{bounded_context}/models.py`
   - Domain interfaces go in `domain/{bounded_context}/protocols.py`
   - Domain services go in `domain/{bounded_context}/services.py` 
   - Technical adapters go in `infrastructure/{bounded_context}/{technology}_adapter.py`
   - Use cases go in `application/use_cases/`
   - CLI commands go in `cli/commands.py`

3. **Implementation Approach**
   - Apply DDD principles as described in the Appendix
   - Focus on domain model correctness first
   - Ensure proper separation between domain, application, and infrastructure
   - Maintain backward compatibility when possible, using adapter pattern
   - Add proper tests for new functionality

4. **Code Review**
   - Run `poetry run ruff check .` and `poetry run ruff format .` before submitting
   - Check for proper error handling with specific exceptions
   - Verify all imports follow the standard library -> third-party -> local pattern
   - Ensure docstrings follow Google style format

### Working with Files

- **Domain Layer**
  - These files should NEVER import from infrastructure or application layers
  - Use Python's typing.Protocol for interfaces
  - Keep domain models as simple dataclasses, preferably immutable (frozen=True)
  - Domain services should only depend on domain models and interfaces

- **Application Layer**
  - Should only import from domain layer, never infrastructure
  - Use dependency injection for infrastructure dependencies
  - Handle orchestration between domain services
  - Implement use cases that correspond to user operations

- **Infrastructure Layer**
  - Implement domain interfaces with specific technologies
  - Keep external dependencies isolated here
  - Use proper error handling to translate infrastructure errors to domain concepts
  - Factory methods should create properly configured instances

- **Interfaces Layer (CLI)**
  - Focus on user interaction and input validation
  - Delegate business logic to application layer
  - Provide clear, useful feedback to users
  - Properly format output for console

### Implementation Patterns

- **Composition over Inheritance**
  - Prefer composition over inheritance for adapter implementations
  - Use delegation to existing services when transitioning
  - Example: `LangChainClaudeAdapter` uses `_llm_service` as a component

- **Backward Compatibility**
  - When refactoring, maintain backward compatibility through:
    1. Re-export of moved models through original module path
    2. Adapter classes that expose the old interface but use new implementation
    3. Deprecation notices in docstrings for future migration
  - Example: The models package re-exports from infrastructure/analysis

- **Progressive Enhancement**
  - Implement changes incrementally, following the ROADMAP.md priorities
  - First get core domain models correct, then refactor infrastructure
  - Add new features at the domain level first, then expose via application and interfaces

- **Testing Strategy**
  - Unit test core domain logic independently
  - Use mocks for infrastructure dependencies
  - Add integration tests for complete use cases
  - Update tests as you refactor code

### Architecture Decision Records

All significant architectural decisions should be documented in Architecture Decision Records (ADRs) located in `docs/adr/`. When making substantial changes:

1. Check if an existing ADR covers the decision area
2. If not, create a new ADR following the template in `docs/adr/README.md`
3. Document:
   - The context and problem being addressed
   - The decision made and alternatives considered
   - Consequences (both positive and negative)
   - Implementation strategy
   - Technical debt created or addressed

This ensures transparency in the development process and provides context for future contributors.

Current ADRs:
- [ADR 0001: Domain-Driven Design Architecture](docs/adr/0001-ddd-architecture.md)
- [ADR 0002: Repository Action Decisions](docs/adr/0002-repository-action-decisions.md)

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

## Technical Debt

### DDD Alignment

- **Legacy Service Layer**: The `services/` folder contains implementations that should be moved to the domain or infrastructure layers following proper DDD boundaries:
  - `services/llm_service.py` → Move to `infrastructure/analysis/llm_service.py`
  - `services/github_service.py` → Move to `infrastructure/source_control/github_service.py`
  - `services/repository_analyzer_service.py` → Split between `application/use_cases/` and `domain/`

- **Application Layer Refinement**:
  - Refactor `app/application_runner.py` to use proper dependency injection
  - Move `app/application_factory.py` to `application/factories.py`
  - Create a command/query separation in the application layer

- **Domain Services**:
  - Create missing domain service in `domain/source_control/services.py`
  - Add proper domain events for cross-bounded context communication
  - Complete domain model for new action recommendations (`recommended_action`)

### Infrastructure Improvements

- **Adapter Composition**: Complete the transition from inheritance to composition:
  - ✅ Completed: Removed legacy `infrastructure/langchain_claude.py` and replaced with composition-based `infrastructure/analysis/langchain_claude_adapter.py`
  - Refactor `infrastructure/github_rest.py` to use composition pattern

- **Repository Pattern**: Implement proper repository pattern for persistent data:
  - Add interfaces in domain layer for data persistence
  - Create repository implementations in infrastructure layer
  - Remove direct file system access from application layer

### Code Quality

- **Test Coverage**: Increase test coverage for:
  - Domain services
  - New adapter implementations
  - Application layer use cases
  - The new action recommendation functionality

- **Documentation**:
  - Update docstrings for all classes/methods to reflect DDD approach
  - Create architecture documentation explaining bounded contexts
  - Add examples for using each analysis action (DELETE/ARCHIVE/EXTRACT/KEEP/PIN)

### CLI Interface

- **Command Structure**:
  - Create proper command structure in `cli/` directory
  - Implement command pattern for CLI operations
  - Add commands for the new repository actions

### Future Enhancements

- **Shared Kernel**: Complete the shared kernel:
  - Move all cross-cutting concerns to `shared/` 
  - Remove `utils/` directory
  - Implement proper value objects for shared concepts

- **Error Handling**: Implement domain-specific exceptions:
  - Create exception hierarchy for each bounded context
  - Use proper error messages that reflect domain concepts
  - Implement consistent error handling across the application

- **Configuration**:
  - Complete environment variable handling
  - Add configuration validation
  - Implement configuration profiles for different environments

## Appendix: Architecture & Design Patterns

### Domain-Driven Design (DDD) Concepts

#### Bounded Contexts
- **Definition**: A logical boundary within which a particular domain model applies.
- **Implementation**: We've divided our system into two bounded contexts:
  - `analysis`: Handles repository evaluation, recommendations, and actions.
  - `source_control`: Deals with GitHub repositories, commits, and contributors.
- **Benefits**: Allows separate teams to work in parallel without conflicts. Simplifies models by limiting scope.

#### Ubiquitous Language
- **Definition**: A shared vocabulary between domain experts and developers.
- **Implementation**: Our models use terms like `Repository`, `Analysis`, `Recommendation` that have precise meanings.
- **Benefits**: Reduces translation errors and misunderstandings between business and technical teams.

#### Domain Models
- **Definition**: Object models that reflect domain concepts rather than technical concerns.
- **Implementation**: 
  - `RepoAnalysis`: Domain aggregate representing an analysis of a repository.
  - `Repository`: Domain aggregate representing a GitHub repository.
- **Benefits**: Makes code more self-explanatory and aligned with business needs.

#### Value Objects
- **Definition**: Immutable objects identified by their attributes, not identity.
- **Implementation**:
  - `Recommendation`: Value object with properties for suggestion, reason, and priority.
  - `LanguageBreakdown`: Value object for programming language statistics.
- **Benefits**: Simplifies testing, prevents unexpected side effects, and makes code more predictable.

#### Aggregates
- **Definition**: Cluster of domain objects treated as a single unit.
- **Implementation**:
  - `RepoAnalysis`: Aggregate root that contains recommendations, strengths, weaknesses.
  - `Repository`: Aggregate root that includes language breakdown and metadata.
- **Benefits**: Ensures consistent data modifications and defines transaction boundaries.

#### Domain Services
- **Definition**: Logic that doesn't naturally fit into entities or value objects.
- **Implementation**: 
  - `AnalysisService`: Contains logic for determining repository actions.
- **Benefits**: Prevents domain models from becoming bloated with business rules.

#### Domain Events
- **Definition**: Something significant that happened in the domain.
- **Implementation**: (Planned) Events for repository state changes.
- **Benefits**: Enables loose coupling between bounded contexts.

### Hexagonal/Onion Architecture (Ports & Adapters)

#### Layers
- **Definition**: Concentric circles of responsibility with dependencies pointing inward.
- **Implementation**:
  - `domain`: Core business logic, independent of frameworks.
  - `application`: Orchestrates domain objects to fulfill use cases.
  - `infrastructure`: Technical implementations of domain interfaces.
  - `interface`: User interfaces (CLI).
- **Benefits**: Isolates domain logic from technical concerns, making it more testable and maintainable.

#### Ports (Interfaces)
- **Definition**: Interfaces defined by the domain for external functionality.
- **Implementation**:
  - `AnalyzerPort`: Domain interface for repository analysis.
  - `source_control/protocols.py`: Domain interfaces for source control operations.
- **Benefits**: Decouples domain from specific implementations.

#### Adapters
- **Definition**: Implementations of ports using specific technologies.
- **Implementation**:
  - `LangChainClaudeAdapter`: Implements `