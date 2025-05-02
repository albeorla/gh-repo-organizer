# Poetry and Virtual Environment Guidelines

This guide outlines best practices for Python package management and development environment using Poetry in this project.

## Core Guidelines

- **Always Use Poetry for Python Package Management**
  - Use `poetry run` to execute commands within the virtual environment
  - Example: `poetry run pytest tests/` instead of just `pytest tests/`
  - Example: `poetry run python -m repo_organizer.cli` instead of just `python -m repo_organizer.cli`

## Project Configuration

- **Python Version**: `>=3.12,<4.0`
- **Main Package**: `repo_organizer` (from `src/` directory)
- **CLI Entry Point**: `repo-analyzer = "repo_organizer.cli:app"`
- **Code Style**: Uses `ruff` with line length of 88

## Key Dependencies

```bash
# Core Dependencies
GitPython = "3.1.44"      # Git operations
langchain = "0.3.24"      # LLM framework
langchain_anthropic = "0.3.12"  # Anthropic integration
pydantic = "2.11.3"       # Data validation
typer = "^0.9.0"         # CLI framework
rich = "^13.0.0"         # Rich terminal output

# Development Dependencies
poetry add --group dev ruff  # Linting/formatting
```

## Virtual Environment Management

- Project uses Poetry's built-in virtual environment management
- Virtual environment is located in `.venv/` directory
- Never use `pip` directly, always use `poetry add` or `poetry remove`
- Example: `poetry add pytest` instead of `pip install pytest`

## Development Setup

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

## Key Files

- `pyproject.toml` - Project dependencies and configuration
- `poetry.lock` - Locked dependency versions
- `.venv/` - Virtual environment directory (git ignored)

## Environment Activation

- Use `poetry shell` to activate virtual environment for interactive use
- Use `poetry run` for single commands
- Always ensure virtual environment is active when:
  - Running tests
  - Installing dependencies
  - Running the repo-analyzer CLI
  - Using development tools (ruff, pytest, etc.)

## Dependency Management

- Add runtime dependencies: `poetry add package-name`
- Add development dependencies: `poetry add --group dev package-name`
- Remove dependencies: `poetry remove package-name`
- Update dependencies: `poetry update`
- Show outdated packages: `poetry show --outdated`

## Testing

```bash
# ✅ DO: Run tests through Poetry
poetry run pytest tests/
poetry run pytest tests/ -v  # Verbose output
poetry run pytest tests/path/to/test.py  # Specific test file

# ❌ DON'T: Run pytest directly
pytest tests/  # Wrong - not using Poetry's virtual env
```

## Code Style

```bash
# ✅ DO: Use ruff through Poetry
poetry run ruff check .  # Check code style
poetry run ruff format .  # Format code

# ❌ DON'T: Run ruff directly
ruff check .  # Wrong - not using Poetry's virtual env
```

## Common Issues and Solutions

- If dependencies seem missing, ensure you're using `poetry run`
- If `poetry install` fails, try removing `.venv/` and retrying
- If Poetry commands fail, check that Poetry is installed and up to date
- If you get Python version conflicts, check your local Python matches pyproject.toml (>=3.12)

## Best Practices

- Keep `pyproject.toml` organized and documented
- Regularly update dependencies with `poetry update`
- Use `poetry export` to generate `requirements.txt` if needed
- Commit both `pyproject.toml` and `poetry.lock`
- Use Poetry's built-in scripts defined in `pyproject.toml`
- Follow the line length limit of 88 characters (configured in ruff) 