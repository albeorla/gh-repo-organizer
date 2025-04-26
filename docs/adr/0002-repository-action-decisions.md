# ADR 0002: Repository Action Decisions

## Status

Accepted

## Date

2025-04-26

## Context

The GitHub Repository Organizer currently analyzes repositories and provides insights, but doesn't offer clear actionable decisions. Users have to manually interpret the analysis results to determine what to do with each repository.

We need a way to make the analysis more actionable by providing explicit recommendations on whether to keep, archive, delete, extract valuable parts, or pin the repository.

## Decision

We will extend the repository analysis model with two new fields:

1. `recommended_action`: An enumerated string value with one of:
   - `"DELETE"`: Repository should be deleted
   - `"ARCHIVE"`: Repository should be archived
   - `"EXTRACT"`: Valuable parts should be extracted
   - `"KEEP"`: Repository should be kept as-is
   - `"PIN"`: Repository should be pinned/featured

2. `action_reasoning`: A string explaining the rationale for the recommended action

These fields will be added to:
- The domain model `RepoAnalysis` 
- The Pydantic model in the infrastructure layer
- The LLM prompt template to elicit these recommendations

Additionally, we'll create a domain service `AnalysisService` with methods to:
- Determine if a repository should be archived
- Determine if a repository should be deleted
- Determine if a repository should be pinned
- Extract high-priority recommendations

## Consequences

### Positive

- More actionable analysis results
- Clear decision guidance for users
- Consistent decision-making logic in the domain layer
- Foundation for automating repository management actions

### Negative

- Backward compatibility concerns for existing analysis reports
- Need to update the LLM prompt and potentially retrain/fine-tune
- Additional complexity in the domain model

## Implementation Strategy

1. Add the new fields to the Pydantic model in the infrastructure layer
2. Update the domain model with getters for these fields
3. Create the `AnalysisService` with decision-making logic
4. Update the LLM prompt to request and reason about the recommended action
5. Add backward compatibility for older analysis objects

## Technical Debt

While implementing this change, we identified several areas of technical debt:

1. The LLM service is currently outside the domain layer, mixing infrastructure concerns
2. We're using inheritance instead of composition in adapter implementations
3. There's no proper repository pattern for persisting analysis results

These will be addressed in subsequent refactorings as documented in ROADMAP.md.