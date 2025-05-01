"""
Authentication middleware for CLI commands.

This module provides a middleware layer for validating user authentication
before executing CLI commands.
"""

from typing import Callable, Optional, Any, Dict, List, Union, cast

import typer
from rich.console import Console

from repo_organizer.domain.core.auth_config import AuthConfig, get_default_config
from repo_organizer.domain.core.auth_service import AuthService
from repo_organizer.infrastructure.logging.auth_logger import AuthLogger
from repo_organizer.utils.logger import Logger


# Create console for rich output to match CLI app
console = Console()


def authenticate_command(
    operation_name: str,
    auth_service: Optional[AuthService] = None,
    auth_config: Optional[AuthConfig] = None,
    auth_logger: Optional[AuthLogger] = None,
) -> Callable:
    """
    Decorator to validate authentication before executing a CLI command.
    
    Args:
        operation_name: Name of the operation to authenticate
        auth_service: Optional custom auth service instance
        auth_config: Optional custom auth configuration
        auth_logger: Optional custom authentication logger
        
    Returns:
        Decorator function that wraps command functions
    """
    def decorator(func: Callable) -> Callable:
        """
        Command decorator that checks authentication before executing the command.
        
        Args:
            func: Command function to wrap
            
        Returns:
            Wrapped function that includes authentication checks
        """
        # Use provided auth_service or create one with the provided auth_config
        service = auth_service or AuthService(auth_config=auth_config)
        
        # Create auth logger or use provided one
        logger = auth_logger or AuthLogger(console=console)
        
        # This is needed to preserve the Typer command's parameters and help text
        typer_callback = getattr(func, "__typer_callback__", None)
        
        def wrapper(*args: List[Any], **kwargs: Dict[str, Any]) -> Any:
            """
            Wrapper function that performs authentication validation.
            
            Args:
                *args: Positional arguments to pass to the wrapped function
                **kwargs: Keyword arguments to pass to the wrapped function
                
            Returns:
                Result of the wrapped function
                
            Raises:
                typer.Exit: If authentication fails
            """
            # Extract username from kwargs
            username = kwargs.get('username')
            
            # Validate the operation - ensure username is str or None
            username_str: Optional[str] = username if username is None else str(username)
            is_valid, error_message = service.validate_operation(operation_name, username_str)
            
            # Log the authentication attempt
            metadata = {
                "command": func.__name__,
                "args_count": len(args),
                "kwargs_keys": ",".join(kwargs.keys())
            }
            logger.log_authentication_attempt(
                operation_name=operation_name,
                username=username_str,
                success=is_valid,
                error_message=error_message if not is_valid else None,
                metadata=metadata
            )
            
            # If authentication fails, display error and exit
            if not is_valid:
                console.print(f"[bold red]Authentication Error:[/] {error_message}")
                console.print(
                    "[yellow]Hint:[/] Provide a valid username with --username option"
                )
                raise typer.Exit(code=1)
            
            # If authentication succeeds, execute the command
            return func(*args, **kwargs)
        
        # Preserve Typer callback for proper CLI integration
        if typer_callback:
            setattr(wrapper, "__typer_callback__", typer_callback)
        
        return wrapper
    
    return decorator


def with_auth_option(app: typer.Typer) -> None:
    """
    Add a global username option to all commands in a Typer app.
    
    This function patches the Typer app to add a --username option to all commands.
    The username is now required for all commands to ensure proper authentication
    and attribution of actions.
    
    Args:
        app: Typer app instance to modify
    """
    # Store the original command decorator
    original_command = app.command
    
    # Define a new command decorator that adds the username option
    def command_with_auth(*args, **kwargs):
        """
        Enhanced command decorator that adds authentication options.
        
        Args:
            *args: Positional arguments to pass to the original decorator
            **kwargs: Keyword arguments to pass to the original decorator
            
        Returns:
            Decorated function with authentication options
        """
        # Get the original decorator
        original_decorator = original_command(*args, **kwargs)
        
        # Define a new decorator that adds the username option
        def decorator_with_auth(func):
            """
            Add authentication options to the command function.
            
            Args:
                func: Command function to decorate
                
            Returns:
                Decorated function with authentication options
            """
            # Add username parameter to the command - now required
            # We need to use a different approach to add the option
            username_option = typer.Option(
                ...,  # ... means required in Typer
                "--username",
                "-u",
                help="GitHub username for authentication and action attribution (required)"
            )
            
            # Create a new function with the username parameter
            # This uses Typer's standard approach for adding options to functions
            if hasattr(func, "__annotations__"):
                func.__annotations__["username"] = Optional[str]  # Make it optional for now
            else:
                func.__annotations__ = {"username": Optional[str]}
                
            # No default value since it's required
            # Store the option information for typer to use
            if not hasattr(func, "__typer_params__"):
                func.__typer_params__ = {}
            func.__typer_params__["username"] = username_option
            
            # Use the function with the added parameter
            enhanced_func = func
            
            # Apply the original decorator
            return original_decorator(enhanced_func)
        
        return decorator_with_auth
    
    # Replace the command decorator with our enhanced version
    # This is safe in Typer as it's a common pattern for modifying command behavior
    setattr(app, "command", command_with_auth)


def validate_command_auth(
    command_name: str,
    username: Optional[str] = None,
    exit_on_failure: bool = True,
    logger: Optional[Logger] = None,
    auth_logger: Optional[AuthLogger] = None,
) -> bool:
    """
    Standalone function to validate authentication for a command outside the decorator pattern.
    
    Args:
        command_name: Name of the command to validate
        username: Username to validate
        exit_on_failure: Whether to exit the program on authentication failure
        logger: Optional standard logger for general output
        auth_logger: Optional authentication logger for security events
        
    Returns:
        True if authentication is valid, False otherwise
        
    Raises:
        typer.Exit: If authentication fails and exit_on_failure is True
    """
    # Create auth service
    service = AuthService()
    
    # Create auth logger if not provided
    auth_log = auth_logger or AuthLogger(console=console, logger=logger)
    
    # Validate the operation - ensure username is str or None
    username_str: Optional[str] = username if username is None else str(username)
    is_valid, error_message = service.validate_operation(command_name, username_str)
    
    # Log the authentication attempt
    metadata = {
        "command": command_name,
        "validation_type": "standalone"
    }
    auth_log.log_authentication_attempt(
        operation_name=command_name,
        username=username_str,
        success=is_valid,
        error_message=error_message if not is_valid else None,
        metadata=metadata
    )
    
    # If authentication fails and exit_on_failure is True, display error and exit
    if not is_valid and exit_on_failure:
        console.print(f"[bold red]Authentication Error:[/] {error_message}")
        console.print(
            "[yellow]Hint:[/] Provide a valid username with --username option"
        )
        raise typer.Exit(code=1)
    
    return is_valid