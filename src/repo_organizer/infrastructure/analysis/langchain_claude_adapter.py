"""LangChain/Anthropic adapter implementing the ``AnalyzerPort`` interface.

This is a composition-based adapter following DDD principles to keep the domain
layer independent of external frameworks.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from repo_organizer.domain.analysis.models import RepoAnalysis
from repo_organizer.domain.analysis.protocols import AnalyzerPort
from repo_organizer.infrastructure.analysis.llm_service import LLMService
from repo_organizer.utils.exceptions import LLMServiceError, RateLimitExceededError

if TYPE_CHECKING:
    from collections.abc import Mapping

    from repo_organizer.utils.logger import Logger
    from repo_organizer.utils.rate_limiter import RateLimiter


class LangChainClaudeAdapter(AnalyzerPort):
    """Adapter that implements the AnalyzerPort using LangChain and Claude.

    This adapter uses composition rather than inheritance, properly separating
    the domain interface from the infrastructure implementation.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "claude-3-7-sonnet-latest",
        temperature: float = 0.2,
        max_tokens: int | None = None,
        top_p: float = 1.0,
        top_k: int | None = None,
        thinking_enabled: bool = True,
        thinking_budget: int = 16000,
        request_timeout: int = 120,
        max_retries: int = 3,
        retry_base_delay: float = 1.0,
        rate_limiter: RateLimiter | None = None,
        logger: Logger | None = None,
        enable_caching: bool = True,
        cache_ttl: int = 3600,  # 1 hour cache by default
    ):
        """Initialize with extended thinking support.

        Args:
            api_key: Anthropic API key
            model_name: Model identifier (default: claude-3-7-sonnet-latest)
            temperature: LLM temperature (0.0-1.0)
            max_tokens: Maximum output tokens (None for model default)
            top_p: Top-p sampling parameter (1.0 for no effect)
            top_k: Top-k sampling parameter (None for no effect)
            thinking_enabled: Whether to enable extended thinking
            thinking_budget: Token budget for thinking
            request_timeout: Timeout for API requests in seconds
            max_retries: Maximum number of retries on failure
            retry_base_delay: Base delay for exponential backoff in seconds
            rate_limiter: Optional rate limiter
            logger: Optional logger
            enable_caching: Whether to enable result caching
            cache_ttl: Time-to-live for cached results in seconds
        """
        # Use composition instead of inheritance
        self._llm_service = LLMService(
            api_key=api_key,
            model_name=model_name,
            temperature=temperature,
            thinking_enabled=thinking_enabled,
            thinking_budget=thinking_budget,
            rate_limiter=rate_limiter,
            logger=logger,
        )

        # Store additional configuration
        self.logger = logger
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        self.request_timeout = request_timeout
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl

        # Extended LLM parameters - will be used when we pass them to LLMService
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.top_k = top_k

        # Metrics for monitoring and debugging
        self._metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retry_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_tokens_used": 0,
            "average_response_time": 0.0,
        }

        # Simple in-memory cache
        self._cache: dict[str, tuple[RepoAnalysis, float]] = {}

        # Log initialization
        if self.logger:
            self.logger.log(
                f"Initialized LangChainClaudeAdapter with model {model_name}, "
                f"temperature {temperature}, thinking {'enabled' if thinking_enabled else 'disabled'} "
                f"(budget: {thinking_budget} tokens)",
                "info",
            )

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _get_cache_key(self, repo_data: dict[str, Any]) -> str:
        """Generate a cache key from repository data.

        Args:
            repo_data: Repository data dictionary

        Returns:
            A string cache key
        """
        # Create a simple hash from key repo fields
        key_fields = ["repo_name", "repo_url", "updated_at", "readme_excerpt"]
        values = []

        for field in key_fields:
            if field in repo_data:
                # Convert to string and take first 100 chars to limit key size
                val = str(repo_data[field])[:100]
                values.append(f"{field}:{val}")

        return "|".join(values)

    def _clean_expired_cache(self) -> None:
        """Remove expired items from cache."""
        if not self.enable_caching:
            return

        current_time = time.time()
        expired_keys = [
            key
            for key, (_, timestamp) in self._cache.items()
            if current_time - timestamp > self.cache_ttl
        ]

        for key in expired_keys:
            del self._cache[key]

        if (
            self.logger
            and expired_keys
            and hasattr(self.logger, "debug_enabled")
            and self.logger.debug_enabled
        ):
            self.logger.log(
                f"Cleaned {len(expired_keys)} expired cache entries",
                "debug",
            )

    def _report_thinking_progress(self, repo_name: str, thinking_text: str) -> None:
        """Report thinking progress from the LLM.

        This method can be used to handle thinking progress streaming from the LLM
        if that feature becomes available in LangChain/Anthropic.

        Args:
            repo_name: Name of the repository being analyzed
            thinking_text: Current thinking text from the LLM
        """
        if self.logger and hasattr(self.logger, "debug_enabled") and self.logger.debug_enabled:
            # For now, we just log the thinking progress
            # First 100 chars of thinking text + ellipsis if longer
            preview = thinking_text[:100] + ("..." if len(thinking_text) > 100 else "")
            self.logger.log(
                f"[{repo_name}] Thinking progress: {preview}",
                level="debug",
            )

    def _execute_with_retry(self, repo_data: dict[str, Any]) -> RepoAnalysis:
        """Execute analysis with exponential backoff retry.

        Args:
            repo_data: Repository data to analyze

        Returns:
            Repository analysis

        Raises:
            LLMServiceError: If all retries fail
        """
        retry_count = 0
        last_exception = None
        success = False

        # Create a clean copy of the repo_data
        data_dict = dict(repo_data)
        repo_name = data_dict.get("repo_name", "unknown")

        # We'll track intermediate failures separately from the main metrics
        intermediate_failures = 0

        # Comprehensive validation of required and optional fields
        required_fields = [
            "repo_name",
            "repo_desc",
            "repo_url",
            "updated_at",
            "readme_excerpt",
        ]
        optional_fields = [
            "is_archived",
            "stars",
            "forks",
            "languages",
            "open_issues",
            "closed_issues",
            "activity_summary",
            "recent_commits_count",
            "contributor_summary",
            "dependency_info",
            "dependency_context",
        ]

        # Check for missing required fields
        missing_fields = [field for field in required_fields if not data_dict.get(field)]

        if missing_fields and self.logger:
            self.logger.log(
                f"Warning: Repository {repo_name} missing required fields: {', '.join(missing_fields)}",
                "warning",
            )

        # First ensure all required fields have values
        for field in required_fields:
            if not data_dict.get(field):
                if field == "repo_name":
                    data_dict["repo_name"] = "Unknown Repository"
                elif field == "repo_desc":
                    data_dict["repo_desc"] = "No description available"
                elif field == "repo_url":
                    data_dict["repo_url"] = "No URL available"
                elif field == "updated_at":
                    data_dict["updated_at"] = "Unknown"
                elif field == "readme_excerpt":
                    data_dict["readme_excerpt"] = "No README content available"

                if (
                    self.logger
                    and hasattr(self.logger, "debug_enabled")
                    and self.logger.debug_enabled
                ):
                    self.logger.log(
                        f"Added default value for required field: {field}",
                        "debug",
                    )

        # Then ensure all optional fields have sensible defaults
        for field in optional_fields:
            if field not in data_dict or data_dict.get(field) is None:
                if field in [
                    "stars",
                    "forks",
                    "open_issues",
                    "closed_issues",
                    "recent_commits_count",
                ]:
                    data_dict[field] = 0
                elif field == "is_archived":
                    data_dict[field] = False
                else:  # Text fields
                    data_dict[field] = f"No {field.replace('_', ' ')} available"

                if (
                    self.logger
                    and hasattr(self.logger, "debug_enabled")
                    and self.logger.debug_enabled
                ):
                    self.logger.log(
                        f"Added default value for optional field: {field}",
                        "debug",
                    )

        # Validate critical content field - readme_excerpt
        if (
            not data_dict.get("readme_excerpt")
            or data_dict.get("readme_excerpt") == "No README content available"
        ) and self.logger:
            self.logger.log(
                f"Warning: Repository {repo_name} has no README content - analysis may be limited",
                "warning",
            )

        # Log the data being sent for analysis (helpful for debugging)
        if self.logger and hasattr(self.logger, "debug_enabled") and self.logger.debug_enabled:
            self.logger.log(
                f"Final repository data for analysis of {repo_name}:",
                "debug",
            )
            self.logger.log(f"Data keys: {list(data_dict.keys())}", "debug")
            for key, value in data_dict.items():
                if key == "readme_excerpt":
                    val_str = str(value) if value is not None else "None"
                    preview = val_str[:150] + ("..." if len(val_str) > 150 else "")
                    self.logger.log(
                        f"- {key} ({len(val_str)} chars): {preview}",
                        "debug",
                    )
                else:
                    self.logger.log(f"- {key}: {value}", "debug")

        # Use configurable base delay and max retries
        for attempt in range(self.max_retries + 1):
            try:
                if self.logger:
                    self.logger.log(
                        f"Analyzing repository: {repo_name} (attempt {attempt + 1}/{self.max_retries + 1})",
                        "info",
                    )

                # Perform the actual analysis
                start_time = time.time()

                # Use the LLM service to get a Pydantic model
                # Pass validated data_dict to ensure all fields are available in the correct format
                pyd_model = self._llm_service.analyze_repository(data_dict)

                # Track response time
                response_time = time.time() - start_time

                # Only update metrics on final success, not intermediate attempts
                if attempt == 0:  # First attempt success
                    self._update_metrics(success=True, response_time=response_time)
                else:  # Success after retry
                    self._metrics["retry_count"] += retry_count
                    self._update_metrics(success=True, response_time=response_time)

                success = True

                if self.logger:
                    self.logger.log(
                        f"Successfully analyzed {repo_name} in {response_time:.2f}s",
                        "success",
                    )

                # Convert to domain dataclass
                from repo_organizer.domain.analysis.models import (
                    RepoAnalysis as DomainRepoAnalysis,
                )

                return DomainRepoAnalysis.from_pydantic(pyd_model)

            except RateLimitExceededError as e:
                # Special handling for rate limit errors - don't retry
                self._update_metrics(success=False)
                last_exception = e
                if self.logger:
                    self.logger.log(f"Rate limit exceeded: {e}", "error")
                # Re-raise without retry
                raise

            except Exception as e:
                # Don't update main metrics for intermediate failures, just track locally
                last_exception = e
                retry_count += 1
                intermediate_failures += 1

                # Log the error
                if self.logger:
                    self.logger.log(
                        f"Error during analysis (attempt {attempt + 1}/{self.max_retries + 1}): {e}",
                        "error",
                    )

                # Check if we should retry
                if attempt < self.max_retries:
                    # Calculate backoff delay: base_delay * 2^attempt with jitter
                    delay = (
                        self.retry_base_delay
                        * (2**attempt)
                        * (0.8 + 0.4 * (hash(str(repo_data)) % 100) / 100)
                    )

                    if self.logger:
                        self.logger.log(f"Retrying in {delay:.2f} seconds...", "info")

                    time.sleep(delay)
                    continue

                # All retries failed
                break

        # If we get here and never succeeded, update the failed metrics once
        if not success:
            self._update_metrics(success=False)
            self._metrics["retry_count"] += retry_count

            # If we get here, all retries have failed
            if last_exception:
                if self.logger:
                    self.logger.log(
                        f"All {self.max_retries} retries failed. Last error: {last_exception}",
                        "error",
                    )

                # Wrap in LLMServiceError for better error handling upstream
                raise LLMServiceError(
                    f"Analysis failed after {self.max_retries} retries",
                ) from last_exception

        # This should never happen since last_exception should be set
        if not success:
            raise LLMServiceError(
                f"Analysis failed after {self.max_retries} retries with unknown error",
            )

    def _update_metrics(self, success: bool, response_time: float = 0.0) -> None:
        """Update the adapter metrics.

        Args:
            success: Whether the request was successful
            response_time: The response time in seconds
        """
        self._metrics["total_requests"] += 1

        if success:
            self._metrics["successful_requests"] += 1

            # Update average response time with running average
            prev_avg = self._metrics["average_response_time"]
            prev_count = self._metrics["successful_requests"] - 1

            if prev_count > 0:
                self._metrics["average_response_time"] = (
                    prev_avg * prev_count + response_time
                ) / self._metrics["successful_requests"]
            else:
                self._metrics["average_response_time"] = response_time
        else:
            self._metrics["failed_requests"] += 1

    def get_metrics(self) -> dict[str, Any]:
        """Get adapter metrics.

        Returns:
            Dictionary of metrics
        """
        return dict(self._metrics)

    # ------------------------------------------------------------------
    # AnalyzerPort implementation
    # ------------------------------------------------------------------

    def analyze(self, repo_data: Mapping[str, Any]) -> RepoAnalysis:
        """Analyze a repository using Claude LLM.

        Args:
            repo_data: A mapping containing repository data

        Returns:
            A domain model RepoAnalysis object
        """
        # Convert to dictionary if not already to allow modifications
        repo_data_dict = dict(repo_data)

        # Get repository name or use a default
        repo_name = repo_data_dict.get("repo_name", "unknown")

        # Log repository analysis initiation
        if self.logger:
            self.logger.log(f"Starting analysis of repository: {repo_name}", "info")

            if hasattr(self.logger, "debug_enabled") and self.logger.debug_enabled:
                # Log comprehensive debug information about data
                self.logger.log(
                    f"Repository data keys: {list(repo_data_dict.keys())}",
                    "debug",
                )

                # Check for required fields
                required_fields = [
                    "repo_name",
                    "repo_desc",
                    "repo_url",
                    "updated_at",
                    "readme_excerpt",
                ]
                optional_fields = [
                    "stars",
                    "forks",
                    "languages",
                    "is_archived",
                    "open_issues",
                    "closed_issues",
                    "activity_summary",
                    "contributor_summary",
                ]

                present_required = [
                    f for f in required_fields if f in repo_data_dict and repo_data_dict.get(f)
                ]
                missing_required = [
                    f
                    for f in required_fields
                    if f not in repo_data_dict or not repo_data_dict.get(f)
                ]
                present_optional = [
                    f for f in optional_fields if f in repo_data_dict and repo_data_dict.get(f)
                ]

                # Log field presence status
                if present_required:
                    self.logger.log(
                        f"Present required fields: {present_required}",
                        "debug",
                    )
                if missing_required:
                    self.logger.log(
                        f"MISSING REQUIRED FIELDS: {missing_required}",
                        "warning",
                    )
                if present_optional:
                    self.logger.log(
                        f"Present optional fields: {present_optional}",
                        "debug",
                    )

                # Log a preview of key fields to verify data integrity
                for field in required_fields:
                    value = repo_data_dict.get(field)
                    if field == "readme_excerpt" and value:
                        val_str = str(value)
                        preview = val_str[:150] + "..." if len(val_str) > 150 else val_str
                        self.logger.log(
                            f"{field} ({len(val_str)} chars): {preview}",
                            "debug",
                        )
                    elif value:
                        self.logger.log(f"{field}: {value}", "debug")
                    else:
                        self.logger.log(f"{field}: MISSING", "warning")

        # Handle caching
        if self.enable_caching:
            # Clean expired cache entries first
            self._clean_expired_cache()

            # Check if we have a cache hit
            cache_key = self._get_cache_key(repo_data_dict)
            if cache_key in self._cache:
                analysis, timestamp = self._cache[cache_key]
                self._metrics["cache_hits"] += 1

                if self.logger:
                    age = time.time() - timestamp
                    self.logger.log(
                        f"Cache hit for {repo_name} (age: {age:.1f}s)",
                        "info",
                    )

                return analysis

            # No cache hit
            self._metrics["cache_misses"] += 1
            if self.logger and hasattr(self.logger, "debug_enabled") and self.logger.debug_enabled:
                self.logger.log(f"Cache miss for {repo_name}", "debug")

        try:
            # Execute analysis with retry logic
            self.logger.log(
                f"Executing analysis for {repo_name} with retry logic",
                "info",
            )
            analysis = self._execute_with_retry(repo_data_dict)

            # Cache successful result if caching is enabled
            if self.enable_caching:
                cache_key = self._get_cache_key(repo_data_dict)
                self._cache[cache_key] = (analysis, time.time())

                if (
                    self.logger
                    and hasattr(self.logger, "debug_enabled")
                    and self.logger.debug_enabled
                ):
                    self.logger.log(
                        f"Cached analysis result for {repo_name}",
                        "debug",
                    )

            return analysis

        except Exception as e:
            # Print a more informative error message
            if self.logger:
                self.logger.log(f"Error during analysis with LLM: {e}", "error")
                if hasattr(e, "__cause__") and e.__cause__:
                    self.logger.log(f"Root cause: {e.__cause__}", "error")

            # Create a fallback analysis for the repository
            fallback_name = repo_data_dict.get("repo_name", "unknown")

            # Try to create a minimal analysis with what we know
            return RepoAnalysis(
                repo_name=fallback_name,
                summary=f"Analysis failed: {e!s}",
                strengths=["Analysis unavailable"],
                weaknesses=["Analysis unavailable"],
                recommendations=[],
                activity_assessment="Unknown (analysis failed)",
                estimated_value="Unknown (analysis failed)",
                tags=["error", "analysis-failed"],
            )
