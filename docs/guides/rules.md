# Rule Structure, Content, and Self-Improvement Guidelines

This document provides universal, tool-agnostic best practices for creating, maintaining, and evolving rules in this project.

## Required Rule Structure

Every rule section must begin with YAML frontmatter:
```markdown
---
description: Clear, one-line description of what the rule enforces
globs: path/to/files/*.ext, other/path/**/*
alwaysApply: boolean
---
```

- Use Markdown with bullet points, sub-points, and code examples
- Reference actual code, other rules, or documentation as needed
- Follow consistent formatting across all rules

## Content Guidelines

- Start with a high-level overview of what the rule enforces and why
- List specific, actionable requirements
- Always provide both DO and DON'T code examples:
  ```typescript
  // ✅ DO: Use clear, actionable examples
  const goodExample = true;

  // ❌ DON'T: Use vague or theoretical anti-patterns
  const badExample = false;
  ```
- Keep rules DRY by referencing related rules or sections

## Best Practices

- Use bullet points and section headers for clarity
- Keep descriptions and requirements concise and unambiguous
- Prefer real code and project examples over theoretical ones
- Use consistent formatting and structure across all rules
- Regularly review rules for relevance and accuracy

## Quality Checklist for Each Rule

- [ ] Clear, one-line description in frontmatter
- [ ] Correct file/section references (use `[filename](mdc:path)` for codebase rules)
- [ ] Both DO and DON'T code examples
- [ ] Actionable and specific requirements
- [ ] Cross-references to related rules/sections
- [ ] Consistent formatting with other rules

## Example Rule Section Template

```markdown
---
description: Enforces snake_case for all Python function and variable names
globs: src/**/*.py
alwaysApply: true
---

- **Use snake_case for all Python function and variable names**
  - Ensures consistency and readability across the codebase
  - Example:
    ```python
    # ✅ DO:
    def my_function():
        my_variable = 1

    # ❌ DON'T:
    def MyFunction():
        MyVariable = 1
    ```
```

## Rule Maintenance and Continuous Improvement

### Rule Improvement Triggers
- New code patterns not covered by existing rules
- Repeated similar implementations across files
- Common error patterns that could be prevented
- New libraries or tools being used consistently
- Emerging best practices in the codebase

### Analysis Process
- Compare new code with existing rules
- Identify patterns that should be standardized
- Look for references to external documentation
- Check for consistent error handling patterns
- Monitor test patterns and coverage

### Rule Updates

**Add New Rules When:**
- A new technology/pattern is used in 3+ files
- Common bugs could be prevented by a rule
- Code reviews repeatedly mention the same feedback
- New security or performance patterns emerge

**Modify Existing Rules When:**
- Better examples exist in the codebase
- Additional edge cases are discovered
- Related rules have been updated
- Implementation details have changed

**Deprecate/Remove Rules When:**
- Patterns are no longer relevant or used
- Rules are superseded by better practices
- Document migration paths for old patterns

### Example Pattern Recognition

```typescript
// If you see repeated patterns like:
const data = await prisma.user.findMany({
  select: { id: true, email: true },
  where: { status: 'ACTIVE' }
});

// Consider adding a section in the rules document:
// - Standard select fields
// - Common where conditions
// - Performance optimization patterns
```

### Documentation Updates
- Keep examples synchronized with code
- Update references to external docs
- Maintain links between related rules
- Document breaking changes 