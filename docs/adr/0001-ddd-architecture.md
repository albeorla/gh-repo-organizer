# ADR 0001: Domain-Driven Design Architecture

## Status

Accepted

## Date

2025-04-26

## Context

The GitHub Repository Organizer has grown organically without strict architectural boundaries, leading to:

1. Mixed responsibilities between layers
2. Difficulty maintaining and extending the codebase
3. Tightly coupled components that are hard to test in isolation
4. Unclear domain models that sometimes contain infrastructure concerns

We need a clear architectural approach that helps us better organize the codebase and make it more maintainable while preserving existing functionality.

## Decision

We will adopt Domain-Driven Design (DDD) with a Hexagonal/Onion Architecture approach:

1. **Domain Layer**
   - Pure business logic with no external dependencies
   - Domain models as immutable dataclasses 
   - Domain services for operations that don't belong to a single entity
   - Interfaces (protocols) defining what the domain needs from outside

2. **Application Layer**
   - Orchestrates domain objects to execute use cases
   - Depends only on the domain layer
   - Handles transactions and cross-cutting concerns

3. **Infrastructure Layer**
   - Implements domain interfaces
   - Contains all external dependencies
   - Provides adapters to external systems

4. **Interface Layer**
   - Command Line Interface (CLI)
   - Presentation logic only

## Consequences

### Positive

- Clearer separation of concerns
- More testable components
- Domain model that better reflects business reality
- Easier to extend with new features
- Better encapsulation of external dependencies

### Negative

- Increased complexity in the short term
- Need for backward compatibility during transition
- More files and potential indirection
- Learning curve for new contributors

## Implementation Strategy

The transition will be incremental:

1. First phase: Create proper bounded contexts and domain model
   - Identify clear boundaries: `analysis` and `source_control`
   - Extract pure domain models into appropriate packages
   - Define interfaces for external dependencies

2. Second phase: Refactor existing services
   - Move infrastructure concerns to proper adapters
   - Create application services that orchestrate domain logic
   - Implement composition-based adapters

3. Third phase: Clean up and remove legacy code
   - Remove redundant or deprecated components
   - Complete documentation
   - Increase test coverage

## Technical Debt Tracking

We will maintain transparency about technical debt through:

1. A dedicated "Technical Debt" section in CLAUDE.md
2. Explicit TODOs in code with links to relevant GitHub issues
3. Deprecation notices in docstrings for components scheduled for removal
4. ROADMAP.md with prioritized tasks using the Eisenhower matrix

All architectural decisions will be documented in ADRs to provide context for future development.