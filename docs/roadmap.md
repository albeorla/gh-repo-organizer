# GitHub Repository Organizer Roadmap

This document outlines the development roadmap for the GitHub Repository Organizer, prioritized using the Eisenhower Matrix to help focus efforts on the most critical tasks.

## Eisenhower Priority Matrix

### Quadrant 1: Urgent & Important

These tasks are critical for core functionality and should be addressed immediately:

- [x] Implement LLM extended thinking support for improved analysis
- [x] Add configurable model selection via environment variables
- [x] Fix bare except blocks in exception handling
- [x] Make DDD approach the only implementation (integrate analyze-ddd)
- [x] Update repo models to support repository actions (DELETE/ARCHIVE/EXTRACT/KEEP/PIN)
- [ ] Create comprehensive test suite for new adapter implementations
- [ ] Remove direct dependency on old LLMService in application layer
- [ ] Update CLI to support repository actions based on analysis results
- [ ] Fix any regressions in the main analysis flow

### Quadrant 2: Important but Not Urgent

These tasks are important for long-term maintainability and should be planned:

- [x] Create domain service for analysis (AnalysisService)
- [x] Implement composition-based LangChainClaudeAdapter
- [x] Document DDD patterns and architecture in CLAUDE.md
- [ ] Complete migration of services to proper DDD layers:
  - [ ] Move `services/llm_service.py` → `infrastructure/analysis/llm_service.py`
  - [ ] Move `services/github_service.py` → `infrastructure/source_control/github_service.py`
  - [ ] Split analyzer service between domain and application layers
- [ ] Implement proper domain events for cross-bounded context communication
- [ ] Create source_control domain services
- [ ] Add proper persistence abstractions using Repository pattern
- [ ] Implement configuration validation for environment variables

### Quadrant 3: Urgent but Not Important

These tasks help with immediate usability but aren't critical to the architecture:

- [x] Create detailed `.env.example` file
- [x] Update documentation for new environment variables
- [ ] Add command-line output for repository actions
- [ ] Improve progress reporting and console output
- [ ] Generate summary reports of action recommendations
- [ ] Add basic filtering options to CLI for viewing different repository actions
- [ ] Script to help users implement recommended actions (archive/delete repositories)

### Quadrant 4: Not Urgent & Not Important

These tasks would be nice to have but should be deferred until higher priorities are completed:

- [ ] Web interface for viewing repository analyses
- [ ] Dashboard for tracking repository metrics
- [ ] Integration with additional LLM providers
- [ ] Support for GitLab and BitBucket repositories
- [ ] GitHub Action for scheduled analysis
- [ ] VSCode extension for viewing analysis results

## Release Plan

### v0.3.0 (Current)
- [x] Consolidate DDD implementation
- [x] Add extended thinking and configurable models
- [x] Fix core bugs and linting issues
- [x] Update Pydantic models and domain model structure

### v0.4.0 (Next)
- [ ] Complete adapter refactoring for composition pattern
- [ ] Add repository action implementation (UI + domain logic)
- [ ] Improve test coverage
- [ ] Provide utilities for implementing recommendations

### v0.5.0
- [ ] Complete migration to proper DDD layering
- [ ] Add domain events and domain services
- [ ] Implement repository pattern for persistence
- [ ] Improve configuration and validation

### v1.0.0
- [ ] Complete documentation
- [ ] Full test coverage
- [ ] Polished user experience
- [ ] Comprehensive CLI features

## Development Guidelines

When implementing these features, follow these guidelines:

1. Maintain backward compatibility when possible
2. Add tests for new functionality
3. Update documentation alongside code changes
4. Follow the DDD principles outlined in the architecture documentation
5. Run `poetry run ruff check .` and `poetry run ruff format .` before committing

## Task Tracking

Use this file to track progress by checking off completed tasks:

- [x] Completed task
- [ ] Pending task

Tasks in Quadrant 1 should take priority over all others, followed by Quadrant 2, then Quadrant 3, and finally Quadrant 4.