# Domain-Driven Design Architecture Guide

This guide explains the architectural patterns and design principles used in the GitHub Repository Organizer project.

## Domain-Driven Design (DDD) Concepts

### Bounded Contexts
- **Definition**: A logical boundary within which a particular domain model applies.
- **Implementation**: We've divided our system into two bounded contexts:
  - `analysis`: Handles repository evaluation, recommendations, and actions.
  - `source_control`: Deals with GitHub repositories, commits, and contributors.
- **Benefits**: Allows separate teams to work in parallel without conflicts. Simplifies models by limiting scope.

### Ubiquitous Language
- **Definition**: A shared vocabulary between domain experts and developers.
- **Implementation**: Our models use terms like `Repository`, `Analysis`, `Recommendation` that have precise meanings.
- **Benefits**: Reduces translation errors and misunderstandings between business and technical teams.

### Domain Models
- **Definition**: Object models that reflect domain concepts rather than technical concerns.
- **Implementation**: 
  - `RepoAnalysis`: Domain aggregate representing an analysis of a repository.
  - `Repository`: Domain aggregate representing a GitHub repository.
- **Benefits**: Makes code more self-explanatory and aligned with business needs.

### Value Objects
- **Definition**: Immutable objects identified by their attributes, not identity.
- **Implementation**:
  - `Recommendation`: Value object with properties for suggestion, reason, and priority.
  - `LanguageBreakdown`: Value object for programming language statistics.
- **Benefits**: Simplifies testing, prevents unexpected side effects, and makes code more predictable.

### Aggregates
- **Definition**: Cluster of domain objects treated as a single unit.
- **Implementation**:
  - `RepoAnalysis`: Aggregate root that contains recommendations, strengths, weaknesses.
  - `Repository`: Aggregate root that includes language breakdown and metadata.
- **Benefits**: Ensures consistent data modifications and defines transaction boundaries.

### Domain Services
- **Definition**: Logic that doesn't naturally fit into entities or value objects.
- **Implementation**: 
  - `AnalysisService`: Contains logic for determining repository actions.
- **Benefits**: Prevents domain models from becoming bloated with business rules.

### Domain Events
- **Definition**: Something significant that happened in the domain.
- **Implementation**: (Planned) Events for repository state changes.
- **Benefits**: Enables loose coupling between bounded contexts.

## Hexagonal/Onion Architecture (Ports & Adapters)

### Layers
- **Definition**: Concentric circles of responsibility with dependencies pointing inward.
- **Implementation**:
  - `domain`: Core business logic, independent of frameworks.
  - `application`: Orchestrates domain objects to fulfill use cases.
  - `infrastructure`: Technical implementations of domain interfaces.
  - `interface`: User interfaces (CLI).
- **Benefits**: Isolates domain logic from technical concerns, making it more testable and maintainable.

### Ports (Interfaces)
- **Definition**: Interfaces defined by the domain for external functionality.
- **Implementation**:
  - `AnalyzerPort`: Domain interface for repository analysis.
  - `source_control/protocols.py`: Domain interfaces for source control operations.
- **Benefits**: Decouples domain from specific implementations.

### Adapters
- **Definition**: Implementations of ports using specific technologies.
- **Implementation**:
  - `LangChainClaudeAdapter`: Implements `AnalyzerPort` using LangChain and Anthropic API.
  - `GitHubRESTAdapter`: Implements source control interfaces using GitHub REST API.
- **Benefits**: Makes it easy to swap out implementations without affecting domain logic.

## SOLID Principles

### Single Responsibility Principle (SRP)
- **Definition**: A class should have only one reason to change.
- **Implementation**:
  - `AnalysisService`: Only responsible for analysis-related business rules.
  - `LangChainClaudeAdapter`: Only responsible for bridging to the LLM API.
- **Benefits**: Makes code more maintainable and reduces side effects of changes.

### Open/Closed Principle (OCP)
- **Definition**: Software entities should be open for extension but closed for modification.
- **Implementation**:
  - Protocol classes define interfaces that can be extended with new implementations.
  - Domain models can be extended with new functionality without changing existing code.
- **Benefits**: New functionality can be added without breaking existing code.

### Liskov Substitution Principle (LSP)
- **Definition**: Subtypes must be substitutable for their base types.
- **Implementation**:
  - Adapter implementations fully satisfy their protocol interfaces.
  - Domain models follow consistent patterns across bounded contexts.
- **Benefits**: Ensures that replacements won't break the code unexpectedly.

### Interface Segregation Principle (ISP)
- **Definition**: No client should be forced to depend on methods it does not use.
- **Implementation**:
  - `AnalyzerPort`: Focused interface with just the analysis method.
  - Service protocols define minimal interfaces needed by consumers.
- **Benefits**: Prevents coupling between unrelated functionality.

### Dependency Inversion Principle (DIP)
- **Definition**: High-level modules should not depend on low-level modules; both should depend on abstractions.
- **Implementation**:
  - Domain and application layers depend on interfaces, not concrete implementations.
  - Protocol classes define abstractions for external dependencies.
- **Benefits**: Facilitates unit testing and allows for swapping implementations.

## Design Patterns

### Strategy Pattern
- **Definition**: Defines a family of algorithms and makes them interchangeable.
- **Implementation**:
  - `LLMService`: Different LLM backends can be used with consistent interface.
- **Benefits**: Allows selecting different algorithms at runtime.

### Adapter Pattern
- **Definition**: Converts the interface of a class into another interface clients expect.
- **Implementation**:
  - `LangChainClaudeAdapter`: Adapts LangChain API to our domain interfaces.
- **Benefits**: Enables integration of incompatible interfaces.

### Factory Method Pattern
- **Definition**: Creates objects without specifying the exact class to create.
- **Implementation**:
  - `ApplicationFactory`: Creates configured application instance.
  - `create_analysis_chain()`: Creates configured LLM chain.
- **Benefits**: Centralizes object creation logic and hides implementation details.

### Façade Pattern
- **Definition**: Provides a simplified interface to a complex subsystem.
- **Implementation**:
  - `ApplicationRunner`: Simplifies the process of running the application.
- **Benefits**: Hides complexity and reduces coupling between subsystems.

### Repository Pattern
- **Definition**: Mediates between domain and data mapping layers.
- **Implementation**:
  - `GitHubService`: Abstracts GitHub API interactions.
  - `Settings`: Abstracts configuration management.
- **Benefits**: Decouples domain logic from data storage concerns.

### Command Pattern
- **Definition**: Encapsulates a request as an object.
- **Implementation**:
  - `ApplicationRunner.run()`: Encapsulates analysis execution.
- **Benefits**: Decouples method invocation from method execution.

### Observer Pattern
- **Definition**: Allows objects to be notified of state changes.
- **Implementation**:
  - `ProgressReporter`: Notifies consumers of progress updates.
- **Benefits**: Enables loose coupling between components.