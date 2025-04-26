# GitHub Repository Organizer Documentation

This directory contains comprehensive documentation for the GitHub Repository Organizer project.

## Overview

The GitHub Repository Organizer is a tool for analyzing and organizing GitHub repositories using AI-powered analysis with Domain-Driven Design architecture. It helps users determine the purpose, value, and potential improvements for their repositories, and provides actionable recommendations.

## Documentation Structure

- **Guides**: Detailed explanations and how-to documentation
  - [Architecture Guide](guides/ddd-architecture.md): Explanation of DDD patterns and principles
  - [Development Guide](guides/development.md): Guide for developers contributing to the project

- **Architecture Decision Records (ADRs)**: Documentation of key architectural decisions
  - [ADR 0001: Domain-Driven Design Architecture](adr/0001-ddd-architecture.md)
  - [ADR 0002: Repository Action Decisions](adr/0002-repository-action-decisions.md)
  - [ADR README](adr/README.md): Template and guidelines for creating new ADRs

- **Roadmap**: Development priorities and upcoming features
  - [Project Roadmap](roadmap.md): Prioritized tasks using Eisenhower Matrix

## Additional Resources

- [README.md](../README.md): Project overview and quickstart guide
- [CLAUDE.md](../CLAUDE.md): Guidance for Claude Code AI when working with this codebase
- [.env.example](../.env.example): Example environment configuration

## Key Concepts

### Domain-Driven Design (DDD)

The project follows DDD principles to ensure that the codebase reflects the business domain. Key DDD concepts used include:

- **Bounded Contexts**: Separate models for `analysis` and `source_control`
- **Domain Models**: Core business entities like `RepoAnalysis` and `Repository`
- **Domain Services**: Pure business logic in services like `AnalysisService`
- **Value Objects**: Immutable objects like `Recommendation`
- **Repositories**: Abstractions for data access

### Hexagonal Architecture (Ports & Adapters)

The codebase is structured using Hexagonal Architecture:

- **Domain**: Core business logic and interfaces
- **Application**: Use cases that orchestrate domain objects
- **Infrastructure**: Technical implementations of domain interfaces
- **Interface**: CLI and other user-facing components

## Contributing to Documentation

When contributing to documentation:

1. Place new guides in the `guides/` directory
2. Document architectural decisions in ADRs under `adr/`
3. Update the main README.md for changes affecting user experience
4. Keep this documentation index updated

## Keeping Documentation Current

Documentation should be updated alongside code changes. When implementing new features or making significant changes:

1. Update relevant guides
2. Create new ADRs for architectural decisions
3. Update the roadmap to reflect progress
4. Ensure code examples match current implementation