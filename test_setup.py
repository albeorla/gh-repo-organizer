#!/usr/bin/env python3
"""
Test script to verify the project setup and configuration.

This script tests:
1. Configuration loading
2. Logging functionality
3. Directory creation
4. Rate limiting
5. Error handling
"""

import os
import sys
import time
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import our components
from repo_organizer.infrastructure.config.settings import Settings, load_settings
from repo_organizer.infrastructure.logging.logger import Logger, create_logger, initialize_directories
from repo_organizer.infrastructure.rate_limiting.rate_limiter import RateLimiter, GitHubRateLimiter, LLMRateLimiter
from repo_organizer.infrastructure.errors.exceptions import RepoOrganizerError, ConfigurationError
from repo_organizer.infrastructure.errors.error_handler import handle_errors, log_error


def test_configuration():
    """Test configuration loading from environment variables."""
    print("\n=== Testing Configuration ===")
    
    # Set test environment variables
    os.environ["GITHUB_TOKEN"] = "test_github_token_12345"
    os.environ["ANTHROPIC_API_KEY"] = "test_anthropic_api_key_67890"
    os.environ["GITHUB_USERNAME"] = "test_user"
    os.environ["OUTPUT_DIR"] = ".test_output"
    os.environ["LOGS_DIR"] = ".test_logs"
    
    # Load settings
    settings = load_settings()
    
    # Verify settings were loaded correctly
    print(f"GitHub Token: {'*' * 10}")
    print(f"GitHub Username: {settings.github_username}")
    print(f"Output Directory: {settings.output_dir}")
    print(f"Logs Directory: {settings.logs_dir}")
    print(f"LLM Model: {settings.llm_model}")
    
    # Verify directory validators
    assert os.path.exists(settings.output_dir), "Output directory was not created"
    assert os.path.exists(settings.logs_dir), "Logs directory was not created"
    
    print("✅ Configuration test passed")
    return settings


def test_logging(settings):
    """Test logging functionality."""
    print("\n=== Testing Logging ===")
    
    # Create logger
    logger = create_logger(settings)
    
    # Test different log levels
    logger.log("This is an info message", level="info")
    logger.log("This is a warning message", level="warning")
    logger.log("This is an error message", level="error")
    logger.log("This is a debug message", level="debug")
    logger.log("This is a success message", level="success")
    
    # Verify log file was created
    log_file = os.path.join(settings.logs_dir, "repo_organizer.log")
    assert os.path.exists(log_file), f"Log file {log_file} was not created"
    
    # Read and print log file contents
    with open(log_file, "r") as f:
        log_content = f.read()
    
    print(f"Log file content ({len(log_content.splitlines())} lines):")
    print(log_content[:300] + "..." if len(log_content) > 300 else log_content)
    
    print("✅ Logging test passed")
    return logger


def test_rate_limiting(logger):
    """Test rate limiting functionality."""
    print("\n=== Testing Rate Limiting ===")
    
    # Create rate limiters
    github_limiter = GitHubRateLimiter(calls_per_minute=60)  # Higher rate for testing
    llm_limiter = LLMRateLimiter(calls_per_minute=30)        # Higher rate for testing
    
    # Test GitHub rate limiter
    print("Testing GitHub rate limiter (5 rapid calls)...")
    start_time = time.time()
    wait_times = []
    
    for i in range(5):
        wait_time = github_limiter.wait(logger=logger, debug=True)
        wait_times.append(wait_time)
        print(f"Call {i+1}: waited {wait_time:.4f}s")
    
    elapsed = time.time() - start_time
    print(f"Total time for 5 GitHub API calls: {elapsed:.4f}s")
    
    # Test LLM rate limiter
    print("\nTesting LLM rate limiter (5 rapid calls)...")
    start_time = time.time()
    wait_times = []
    
    for i in range(5):
        wait_time = llm_limiter.wait(logger=logger, debug=True)
        wait_times.append(wait_time)
        print(f"Call {i+1}: waited {wait_time:.4f}s")
    
    elapsed = time.time() - start_time
    print(f"Total time for 5 LLM API calls: {elapsed:.4f}s")
    
    # Print statistics
    print("\nRate limiting statistics:")
    print(f"GitHub stats: {github_limiter.get_stats()}")
    print(f"LLM stats: {llm_limiter.get_stats()}")
    
    print("✅ Rate limiting test passed")


def test_error_handling(logger):
    """Test error handling functionality."""
    print("\n=== Testing Error Handling ===")
    
    # Define a test function that will raise an exception
    @handle_errors(logger, default_message="Test function failed", reraise=False)
    def test_function(should_fail=True):
        if should_fail:
            raise ConfigurationError("This is a test error")
        return "Success"
    
    # Test with error
    print("Testing with error...")
    result = test_function(should_fail=True)
    print(f"Result with error: {result}")
    
    # Test without error
    print("\nTesting without error...")
    result = test_function(should_fail=False)
    print(f"Result without error: {result}")
    
    # Test manual error logging
    print("\nTesting manual error logging...")
    try:
        raise RepoOrganizerError("Manual test error")
    except Exception as e:
        log_error(logger, e, message="Manual error occurred", log_level="error")
    
    print("✅ Error handling test passed")


def main():
    """Run all tests."""
    print("Starting setup verification tests...\n")
    
    try:
        # Run tests
        settings = test_configuration()
        logger = test_logging(settings)
        test_rate_limiting(logger)
        test_error_handling(logger)
        
        # Print summary
        print("\n=== All Tests Passed ===")
        print("Project setup verification successful!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Clean up test files
    print("\nCleaning up test files...")
    if os.path.exists(".test_output"):
        os.rmdir(".test_output")
    if os.path.exists(".test_logs"):
        import shutil
        shutil.rmtree(".test_logs")


if __name__ == "__main__":
    main()