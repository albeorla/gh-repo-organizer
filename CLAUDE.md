---
description: Unified guidelines for development workflow, rule creation, and maintenance in this repository, focused on Claude Code.
globs: **/*
alwaysApply: true
---

# Claude Code Project Guide

This document provides actionable guidelines for:
- Using [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview) as your agentic coding tool
- Setting up, configuring, and maintaining your project with Claude Code
- Creating, maintaining, and evolving rules and workflows for effective AI-assisted development
- Ensuring security, clarity, and continuous improvement across the codebase

---

## 1. Claude Code Overview

[Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview) is an agentic coding tool by Anthropic that operates directly in your terminal, understands your codebase, and helps you code faster through natural language commands. It streamlines your workflow without requiring additional servers or complex setup.

**Key Capabilities:**
- Editing files and fixing bugs across your codebase
- Answering questions about your code's architecture and logic
- Executing and fixing tests, linting, and other commands
- Searching through git history, resolving merge conflicts, and creating commits and PRs
- Automating CI and infra workflows (non-interactive mode)

**Security and Privacy:**
- Direct API connection to Anthropic (no intermediate servers)
- Operates in your terminal, maintaining project context
- Strict privacy safeguards and limited data retention ([see docs](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview#security-and-privacy-by-design))

---

## 2. Setup and Authentication

1. **Install Node.js 18+**
2. **Install Claude Code globally:**
   ```sh
   npm install -g @anthropic-ai/claude-code
   ```
   *Do NOT use `sudo npm install -g`.*
3. **Navigate to your project:**
   ```sh
   cd your-project-directory
   ```
4. **Start Claude Code:**
   ```sh
   claude
   ```
5. **Authenticate:**
   - Follow the OAuth process with your Anthropic Console account (active billing required).

For troubleshooting installation or authentication, see [Claude Code Troubleshooting](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/troubleshooting).

---

## 3. Core Features and Workflows

Claude Code operates directly in your terminal, understanding your project context and taking real actions. No need to manually add files to context—Claude will explore your codebase as needed.

### Common Use Cases
- **Understand unfamiliar code:**
  ```
  claude
  > what does the payment processing system do?
  > find where user permissions are checked
  > explain how the caching layer works
  ```
- **Automate Git operations:**
  ```
  > commit my changes
  > create a pr
  > which commit added tests for markdown back in December?
  > rebase on main and resolve any merge conflicts
  ```
- **Edit code intelligently:**
  ```
  > add input validation to the signup form
  > refactor the logger to use the new API
  > fix the race condition in the worker queue
  ```
- **Test and debug your code:**
  ```
  > run tests for the auth module and fix failures
  > find and fix security vulnerabilities
  > explain why this test is failing
  ```
- **Encourage deeper thinking:**
  ```
  > think about how we should architect the new payment service
  > think hard about the edge cases in our authentication flow
  ```
  - Use "think" or "think hard" to trigger extended planning ([see tips](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview#encourage-deeper-thinking)).
- **Automate CI and infra workflows:**
  - Use non-interactive mode with `claude -p "<command>"` for scripts and pipelines.

---

## 4. CLI Commands and Usage Patterns

Claude Code provides a rich CLI for interactive and non-interactive use. See the [official CLI command reference](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview#cli-commands).

| Command                       | Description                              | Example                                                                                                 |
| ----------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| claude                        | Start interactive REPL                   | claude                                                                                                  |
| claude "query"                | Start REPL with initial prompt           | claude "how does our authentication system work?"                                                      |
| claude commit                 | Create a commit                          | claude commit                                                                                           |
| claude -p "<command>"         | Non-interactive mode (for CI/scripts)    | claude -p "update the README with the latest changes"                                                  |

For more, see [Claude Code Tutorials](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/tutorials).

---

## 5. Environment Variables and Configuration

- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
- `CLAUDE_CODE_USE_BEDROCK=1`: Use Amazon Bedrock as backend ([see docs](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview#connect-to-amazon-bedrock))
- `CLAUDE_CODE_USE_VERTEX=1`: Use Google Vertex AI as backend ([see docs](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview#connect-to-google-vertex-ai))
- `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_CUSTOM_HEADERS`, `HTTP_PROXY`, `HTTPS_PROXY`: Proxy and custom header support
- For full configuration options, see [Claude Code Configuration](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview#environment-variables)

---

## 6. Rule Structure, Content, and Self-Improvement Guidelines

This section provides universal, tool-agnostic best practices for creating, maintaining, and evolving rules in this document or any rules file in your project.

---

### Required Rule Structure
- Every rule section must begin with YAML frontmatter:
  ```markdown
  ---
  description: Clear, one-line description of what the rule enforces
  globs: path/to/files/*.ext, other/path/***
  alwaysApply: boolean
  ---
  ```
- Use Markdown with bullet points, sub-points, and code examples.
- Reference actual code, other rules, or documentation as needed.

### Content Guidelines
- Start with a high-level overview of what the rule enforces and why.
- List specific, actionable requirements.
- Always provide both DO and DON'T code examples:
  ```typescript
  // ✅ DO: Use clear, actionable examples
  const goodExample = true;

  // ❌ DON'T: Use vague or theoretical anti-patterns
  const badExample = false;
  ```
- Keep rules DRY by referencing related rules or sections.

### Best Practices
- Use bullet points and section headers for clarity.
- Keep descriptions and requirements concise and unambiguous.
- Prefer real code and project examples over theoretical ones.
- Use consistent formatting and structure across all rules.
- Regularly review rules for relevance and accuracy.

### Quality Checklist for Each Rule
- [ ] Clear, one-line description in frontmatter
- [ ] Correct file/section references (use `[filename](mdc:path)` for codebase rules)
- [ ] Both DO and DON'T code examples
- [ ] Actionable and specific requirements
- [ ] Cross-references to related rules/sections
- [ ] Consistent formatting with other rules

### Example Rule Section Template
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

---

### Rule Maintenance and Continuous Improvement

#### Rule Improvement Triggers
- New code patterns not covered by existing rules
- Repeated similar implementations across files
- Common error patterns that could be prevented
- New libraries or tools being used consistently
- Emerging best practices in the codebase

#### Analysis Process
- Compare new code with existing rules
- Identify patterns that should be standardized
- Look for references to external documentation
- Check for consistent error handling patterns
- Monitor test patterns and coverage

#### Rule Updates
- **Add New Rules When:**
  - A new technology/pattern is used in 3+ files
  - Common bugs could be prevented by a rule
  - Code reviews repeatedly mention the same feedback
  - New security or performance patterns emerge
- **Modify Existing Rules When:**
  - Better examples exist in the codebase
  - Additional edge cases are discovered
  - Related rules have been updated
  - Implementation details have changed
- **Deprecate/Remove Rules When:**
  - Patterns are no longer relevant or used
  - Rules are superseded by better practices
  - Document migration paths for old patterns

#### Example Pattern Recognition
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

#### Documentation Updates
- Keep examples synchronized with code
- Update references to external docs
- Maintain links between related rules
- Document breaking changes

---

## 7. Temporary Test Scripts: Deletion and Archiving

---
description: Ensure temporary test scripts are deleted or archived to keep the codebase clean
globs: *.py,*.sh
alwaysApply: false
---

- **Delete or Archive Temporary Test Scripts**
  - After creating a file for testing (such as a Python or shell script), you must either:
    - Delete the file when it is no longer needed, **or**
    - Move it to a conventional archive directory (e.g., `.archived/`)
  - If using an archive directory:
    - Ensure `.archived/` is added to `.gitignore` to prevent accidental commits
    - Use a consistent location for all archived scripts
- **Examples:**
  - ✅ DO: Remove `verify_structure.py` after verifying project structure
  - ✅ DO: Move `test_script.sh` to `.archived/test_script.sh` if you want to keep it for reference
  - ❌ DON'T: Leave unused test scripts in the main codebase
- **Rationale:**
  - Keeps the codebase clean and free of clutter
  - Prevents confusion over which scripts are production vs. temporary
  - Reduces risk of accidentally running or committing obsolete scripts
- **References:**
  - See [dev_workflow.mdc](mdc:dev_workflow.mdc) for standard development workflow
  - See [.gitignore](mdc:.gitignore) for ignored files

---

## 8. Poetry and Virtual Environment Guidelines

---
description: Best practices for Python package management and development environment using Poetry
globs: **/*
alwaysApply: true
---

# Poetry and Virtual Environment Guidelines

- **Always Use Poetry for Python Package Management**
  - Use `poetry run` to execute commands within the virtual environment
  - Example: `poetry run pytest tests/` instead of just `pytest tests/`
  - Example: `poetry run python -m repo_organizer.cli` instead of just `python -m repo_organizer.cli`

- **Project-Specific Configuration**
  - Python version: `>=3.12,<4.0`
  - Main package: `repo_organizer` (from `src/` directory)
  - CLI entry point: `repo-analyzer = "repo_organizer.cli:app"`
  - Code style: Uses `ruff` with line length of 88

- **Key Dependencies**
  ```bash
  # ✅ DO: Core Dependencies
  GitPython = "3.1.44"      # Git operations
  langchain = "0.3.24"      # LLM framework
  langchain_anthropic = "0.3.12"  # Anthropic integration
  pydantic = "2.11.3"       # Data validation
  typer = "^0.9.0"         # CLI framework
  rich = "^13.0.0"         # Rich terminal output
  
  # ✅ DO: Development Dependencies
  poetry add --group dev ruff  # Linting/formatting
  ```

- **Virtual Environment Management**
  - Project uses Poetry's built-in virtual environment management
  - Virtual environment is located in `.venv/` directory
  - Never use `pip` directly, always use `poetry add` or `poetry remove`
  - Example: `poetry add pytest` instead of `pip install pytest`

- **Development Setup**
  ```bash
  # ✅ DO: Use Poetry commands
  poetry install  # Install dependencies
  poetry shell    # Activate virtual environment
  poetry run pytest tests/  # Run tests
  poetry run repo-analyzer  # Run CLI tool
  poetry add package-name  # Add new dependency
  poetry add --group dev package-name  # Add dev dependency
  
  # ❌ DON'T: Use pip or direct Python commands
  pip install -r requirements.txt  # Wrong
  python -m pytest  # Wrong without poetry run
  ```

- **Key Files**
  - [pyproject.toml](mdc:pyproject.toml) - Project dependencies and configuration
  - [poetry.lock](mdc:poetry.lock) - Locked dependency versions
  - `.venv/` - Virtual environment directory (git ignored)

- **Environment Activation**
  - Use `poetry shell` to activate virtual environment for interactive use
  - Use `poetry run` for single commands
  - Always ensure virtual environment is active when:
    - Running tests
    - Installing dependencies
    - Running the repo-analyzer CLI
    - Using development tools (ruff, pytest, etc.)

- **Dependency Management**
  - Add runtime dependencies: `poetry add package-name`
  - Add development dependencies: `poetry add --group dev package-name`
  - Remove dependencies: `poetry remove package-name`
  - Update dependencies: `poetry update`
  - Show outdated packages: `poetry show --outdated`

- **Testing**
  ```bash
  # ✅ DO: Run tests through Poetry
  poetry run pytest tests/
  poetry run pytest tests/ -v  # Verbose output
  poetry run pytest tests/path/to/test.py  # Specific test file
  
  # ❌ DON'T: Run pytest directly
  pytest tests/  # Wrong - not using Poetry's virtual env
  ```

- **Code Style**
  ```bash
  # ✅ DO: Use ruff through Poetry
  poetry run ruff check .  # Check code style
  poetry run ruff format .  # Format code
  
  # ❌ DON'T: Run ruff directly
  ruff check .  # Wrong - not using Poetry's virtual env
  ```

- **Common Issues**
  - If dependencies seem missing, ensure you're using `poetry run`
  - If `poetry install` fails, try removing `.venv/` and retrying
  - If Poetry commands fail, check that Poetry is installed and up to date
  - If you get Python version conflicts, check your local Python matches pyproject.toml (>=3.12)

- **Best Practices**
  - Keep `pyproject.toml` organized and documented
  - Regularly update dependencies with `poetry update`
  - Use `poetry export` to generate `requirements.txt` if needed
  - Commit both `pyproject.toml` and `poetry.lock`
  - Use Poetry's built-in scripts defined in `pyproject.toml`
  - Follow the line length limit of 88 characters (configured in ruff)

---

## 9. Continuous Improvement and Troubleshooting

- **Improvement Triggers**
  - New code patterns or technologies in 3+ files
  - Repeated feedback in code reviews
  - Common bugs or error patterns
  - Major refactors or new best practices

- **Update Process**
  - Compare new code with existing rules
  - Add, modify, or deprecate rules as needed
  - Cross-reference related or updated rules
  - Add real code examples from the codebase
  - Remove outdated or obsolete rules
  - Mark deprecated rules and provide migration paths
  - Keep examples and references synchronized with the codebase
  - Document breaking changes and major updates

- **Continuous Improvement**
  - Monitor code review comments and implementation logs
  - Update rules after sprints, merges, or onboarding
  - See [Claude Code Tutorials](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/tutorials) and [Troubleshooting](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/troubleshooting) for more

---

## 10. Advanced: Model Context Protocol (MCP)

Claude Code supports advanced workflows and tool integrations via the [Model Context Protocol (MCP)](https://docs.anthropic.com/en/docs/agents-and-tools/mcp). MCP enables structured tool use, memory management, and advanced agentic behaviors.

---

## 11. References and Further Reading

- [Claude Code Overview](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview)
- [Claude Code Tutorials](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/tutorials)
- [Claude Code Troubleshooting](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/troubleshooting)
- [Model Context Protocol (MCP)](https://docs.anthropic.com/en/docs/agents-and-tools/mcp)

---

By following these Claude Code-centric meta-rules and workflow guidelines, you ensure that all code, rules, and processes in this repository are clear, maintainable, and effective for both human and AI contributors.


