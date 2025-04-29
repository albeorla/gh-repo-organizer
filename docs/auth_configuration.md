# Authentication Configuration

This document explains how to configure authentication requirements in the Repository Organizer application.

## Overview

The authentication system allows you to specify which operations require a valid username before execution. Operations are categorized into four types:

- **READ_ONLY**: Operations that only read data (e.g., viewing repositories, reports)
- **ANALYSIS**: Operations that analyze repositories
- **WRITE**: Operations that write or modify data
- **ADMIN**: Administrative operations

Each operation type has a default authentication requirement:

- **REQUIRED**: Authentication is always required
- **OPTIONAL**: Authentication is optional
- **NOT_REQUIRED**: Authentication is not required

## Default Configuration

By default:

- READ_ONLY operations do not require authentication
- ANALYSIS operations require authentication
- WRITE operations require authentication
- ADMIN operations require authentication

## Configuration Methods

You can customize the authentication requirements in several ways:

### 1. Environment Variables

Set the following environment variables to customize authentication:

```bash
# Enable/disable authentication globally (default: true)
AUTH_ENABLED=true

# Override default requirements by operation type (comma-separated list)
AUTH_DEFAULT_REQUIREMENTS=read_only:optional,analysis:required,write:required,admin:required

# Override requirements for specific operations (comma-separated list)
AUTH_OPERATION_OVERRIDES=analyze:not_required,cleanup:required
```

### 2. Configuration File

You can create a `.env` file in the project root with the same variables:

```
AUTH_ENABLED=true
AUTH_DEFAULT_REQUIREMENTS=read_only:optional,analysis:required,write:required,admin:required
AUTH_OPERATION_OVERRIDES=analyze:not_required,cleanup:required
```

### 3. Programmatically

You can create and modify an `AuthConfig` object directly in code:

```python
from repo_organizer.domain.core.auth_config import AuthConfig, AuthRequirement, OperationType

# Create a custom config
config = AuthConfig()

# Modify default requirements
config.default_requirements[OperationType.READ_ONLY] = AuthRequirement.REQUIRED

# Add specific operation overrides
config.operation_overrides["analyze"] = AuthRequirement.NOT_REQUIRED
```

## Operation Categories

The following operations are categorized by default:

### READ_ONLY Operations
- `list_repositories`
- `view_report`
- `view_logs`

### ANALYSIS Operations
- `analyze`
- `generate_report`

### WRITE Operations
- `cleanup`
- `reset`

### ADMIN Operations
- `delete_repository`
- `archive_repository`
- `execute_actions`

## Custom Operation Categories

You can add new operations or change the category of existing operations by customizing the `operation_categories` dictionary:

```python
from repo_organizer.domain.core.auth_config import AuthConfig, OperationType

config = AuthConfig()
config.operation_categories["my_custom_operation"] = OperationType.WRITE
```

## Validating Operations

To check if an operation requires authentication and validate the provided username:

```python
from repo_organizer.domain.core.auth_service import AuthService

# Create auth service
auth_service = AuthService()

# Validate operation with username
is_valid, error_message = auth_service.validate_operation("analyze", "username")

if not is_valid:
    print(f"Error: {error_message}")
else:
    print("Operation is allowed")

# Simplified check
if auth_service.is_operation_allowed("analyze", "username"):
    print("Operation is allowed")
else:
    print("Operation is not allowed")
```

## Integration with CLI Commands

The authentication system is integrated with the CLI commands through a middleware pattern. Each command checks if authentication is required before execution.

Example for a CLI command:

```python
@app.command()
def analyze(..., username: str = typer.Option(..., help="GitHub username")):
    # Validate authentication
    auth_service = AuthService()
    is_valid, error_message = auth_service.validate_operation("analyze", username)
    
    if not is_valid:
        console.print(f"[red]Error: {error_message}[/]")
        raise typer.Exit(1)
    
    # Continue with command execution
    ...
```