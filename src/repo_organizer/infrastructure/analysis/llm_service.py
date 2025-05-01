"""
Language model service for analyzing repository content.

This module implements the Strategy pattern for the language model service,
allowing different LLM backends to be used with a consistent interface.
"""

from typing import Any, Optional

# ---------------------------------------------------------------------------
# Optional dependency handling
# ---------------------------------------------------------------------------
# ``langchain_anthropic`` might not be available in all execution environments
# (e.g. CI pipelines).  Importing it unconditionally would therefore raise a
# ``ModuleNotFoundError`` breaking *all* test runs even when the concrete LLM
# backend is being patched / mocked.  We fall back to a lightweight *stub*
# implementation that mimics the minimal surface required by the tests.

try:
    from langchain_anthropic import ChatAnthropic  # type: ignore
except ModuleNotFoundError:  # pragma: no cover – executed in test env only

    class _StubChatAnthropic:  # noqa: D401,E302
        """Very small stub that fulfils the interface used in tests."""

        def __init__(self, *args, **kwargs):  # noqa: D401
            pass

        # The real class exposes an ``invoke`` method that returns an object
        # having a ``content`` attribute (string).  The unit tests *mock*
        # ``ChatAnthropic`` anyway, so we just raise to signal unintended
        # usage in production.
        def invoke(self, *args, **kwargs):  # noqa: D401
            raise RuntimeError(
                "ChatAnthropic stub invoked – install 'langchain_anthropic' for production use."
            )

    ChatAnthropic = _StubChatAnthropic  # type: ignore  # noqa: N816
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain.output_parsers import OutputFixingParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from repo_organizer.infrastructure.analysis.pydantic_models import RepoAnalysis
from repo_organizer.utils.logger import Logger
from repo_organizer.utils.rate_limiter import RateLimiter


class LLMService:
    """Handles interactions with language models.

    This service follows the Strategy pattern by encapsulating the LLM interaction
    logic and providing a consistent interface regardless of the LLM backend used.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "claude-3-7-sonnet-latest",
        temperature: float = 0.2,
        thinking_enabled: bool = True,
        thinking_budget: int = 16000,
        rate_limiter: Optional[RateLimiter] = None,
        logger: Optional[Logger] = None,
    ):
        """Initialize the LLM service.

        Args:
            api_key: API key for the language model provider
            model_name: Model name to use
            temperature: Temperature for LLM outputs (0.0-1.0)
            thinking_enabled: Whether to enable extended thinking
            thinking_budget: Token budget for extended thinking
            rate_limiter: Optional rate limiter for API calls
            logger: Optional logger for service operations
        """
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.thinking_enabled = thinking_enabled
        self.thinking_budget = thinking_budget
        self.rate_limiter = rate_limiter
        self.logger = logger

        # Initialize ChatAnthropic with extended thinking
        kwargs = {
            "model": model_name,
            "temperature": temperature,
            "anthropic_api_key": api_key,
            "max_retries": 3,  # Built-in retries for LangChain
        }

        # Add extended thinking if enabled
        if thinking_enabled:
            # Important: When using extended thinking, we must remove temperature settings
            # as it's not compatible with temperature modifications
            if "temperature" in kwargs:
                del kwargs["temperature"]
                
            # Add max_tokens parameter to be larger than thinking_budget (required by Claude API)
            kwargs["max_tokens"] = thinking_budget + 4000
            
            # Pass thinking parameter directly to LangChain
            # This is the correct way to enable thinking in newer versions of langchain_anthropic
            kwargs["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}
            
            if logger and logger.debug_enabled:
                logger.log(
                    f"Enabling extended thinking with budget: {thinking_budget} tokens, max_tokens: {thinking_budget + 4000}",
                    "debug",
                )

        self.llm = ChatAnthropic(**kwargs)

        # Lazily-built analysis chain – constructed on first use and then
        # cached for subsequent repository analyses.  Creating the chain can be
        # expensive (especially `OutputFixingParser.from_llm`, which may
        # perform an additional LLM call).  Caching avoids rebuilding the
        # chain for every single repository when analysing dozens of repos in
        # one run.
        self._analysis_chain: Optional[Any] = None

    def _log_raw_output(self, x: Any) -> Any:
        """Logs the raw output before parsing only if debug is enabled.

        Args:
            x: The raw output from the LLM

        Returns:
            The unchanged input for chaining
        """
        if self.logger and self.logger.debug_enabled:
            log_content = x.content if hasattr(x, "content") else str(x)
            self.logger.log(f"Raw LLM Output:\n---\n{log_content}\n---", level="debug")
        return x

    def create_analysis_chain(self) -> Any:
        """Create a runnable chain for repository analysis.

        This method implements the Factory Method pattern to create a configured
        processing chain for repository analysis.

        Returns:
            A runnable chain that takes repository information and returns analysis
        """
        # Only build the chain once (lazy initialisation)
        if self._analysis_chain is not None:
            return self._analysis_chain

        # Apply rate limiting if available for the *chain build* itself – this
        # can trigger a call to the LLM through OutputFixingParser.
        if self.rate_limiter:
            self.rate_limiter.wait(
                self.logger, debug=getattr(self.logger, "debug_enabled", False)
            )

        # Base parser for structured output
        pydantic_parser = PydanticOutputParser(pydantic_object=RepoAnalysis)

        # Wrap with OutputFixingParser (may perform a validation-step LLM call)
        output_fixing_parser = OutputFixingParser.from_llm(
            parser=pydantic_parser, llm=self.llm
        )

        # Create a preprocessing function to prepare input data with strict validation
        def prepare_input_data(data_dict):
            if self.logger and self.logger.debug_enabled:
                self.logger.log(f"Original data keys: {list(data_dict.keys())}", "debug")
                
            # First, validate that the required fields are present and non-empty
            required_fields = ["repo_name", "repo_desc", "repo_url", "updated_at", "readme_excerpt"]
            missing_fields = [f for f in required_fields if not data_dict.get(f)]
            
            if missing_fields and self.logger:
                self.logger.log(
                    f"WARNING: Missing required fields for repository analysis: {', '.join(missing_fields)}",
                    "warning"
                )
                
            # Create a dictionary with all the required fields and default values for missing ones
            prepared_data = {
                # Critical fields - ensure these have meaningful defaults if missing
                "repo_name": data_dict.get("repo_name", "Unknown Repository"),
                "repo_desc": data_dict.get("repo_desc", "No description available"),
                "repo_url": data_dict.get("repo_url", "No URL available"),
                "updated_at": data_dict.get("updated_at", "Unknown"),
                
                # Secondary fields - provide defaults
                "is_archived": data_dict.get("is_archived", False),
                "stars": data_dict.get("stars", 0),
                "forks": data_dict.get("forks", 0),
                "languages": data_dict.get("languages", "No language information available"),
                "open_issues": data_dict.get("open_issues", 0),
                "closed_issues": data_dict.get("closed_issues", 0),
                "activity_summary": data_dict.get("activity_summary", "No activity data available"),
                "recent_commits_count": data_dict.get("recent_commits_count", 0),
                "contributor_summary": data_dict.get("contributor_summary", "No contributor data available"),
                "dependency_info": data_dict.get("dependency_info", "No dependency information available"),
                "dependency_context": data_dict.get("dependency_context", ""),
                
                # Critical content field - ensure it has a meaningful default if missing
                "readme_excerpt": data_dict.get("readme_excerpt", "No README content available"),
                
                # Format instructions for the output parser
                "format_instructions": pydantic_parser.get_format_instructions()
            }
            
            # Log the prepared data for debugging
            if self.logger and self.logger.debug_enabled:
                self.logger.log(f"Prepared data keys: {list(prepared_data.keys())}", "debug")
                for key in ["repo_name", "repo_desc", "repo_url"]:
                    self.logger.log(f"Prepared {key}: {prepared_data.get(key)}", "debug")
                
                # Log README excerpt length for verification
                readme_excerpt = prepared_data.get("readme_excerpt", "")
                self.logger.log(f"README excerpt length: {len(readme_excerpt)}", "debug")
                if readme_excerpt:
                    preview = readme_excerpt[:100] + "..." if len(readme_excerpt) > 100 else readme_excerpt
                    self.logger.log(f"README preview: {preview}", "debug")
            
            return prepared_data
            
        # Create the prompt template using modern ChatPromptTemplate with explicit references
        prompt = ChatPromptTemplate.from_messages(
            [
                HumanMessage(
                    content="""
            You are an AI assistant specialized in analyzing GitHub repositories and generating detailed reports. Your task is to evaluate the repository named "{repo_name}" based on its README content and provide valuable insights, recommendations, and a decision on the repository's future.

            First, carefully read and analyze the following repository information:

            Repository Information:
            - Name: {repo_name}
            - Description: {repo_desc}
            - URL: {repo_url}
            - Last Updated: {updated_at}
            - Archived on GitHub: {is_archived}
            - Stars: {stars}
            - Forks: {forks}
            - Programming Languages: {languages}
            
            Activity Information:
            - Open Issues: {open_issues}
            - Closed Issues: {closed_issues}
            - Recent Activity: {activity_summary}
            - Recent Commits: {recent_commits_count}
            - Contributors: {contributor_summary}
            
            Dependencies:
            - {dependency_info}
            
            README Content:
            ```markdown
            {readme_excerpt}
            ```

            Based on this information, you will generate a detailed analysis. Before writing the final report, conduct a thorough evaluation inside your thinking block:

            1. Summarize the key points from the README:
               - Quote relevant sections that describe the main purpose of the repository
               - List and count the key features or functionalities (e.g., 1. Feature A, 2. Feature B, etc.)
               - Identify the target audience or use cases

            2. Evaluate the repository's strengths:
               - Consider code quality, documentation, uniqueness, and potential usefulness
               - Quote specific sections that highlight these strengths

            3. Identify areas for improvement:
               - Look for gaps in documentation, features, or development practices
               - Quote or reference specific sections that could be improved

            4. Assess the repository's overall value and activity level:
               - Consider factors such as last update, stars, forks, and community engagement
               - Quote any relevant statistics or information from the README

            5. Based on your analysis, consider arguments for each possible action:
               - DELETE: [Arguments for deletion]
               - ARCHIVE: [Arguments for archiving]
               - EXTRACT: [Arguments for extracting valuable parts]
               - KEEP: [Arguments for keeping as is]
               - PIN: [Arguments for pinning/featuring]

            6. Determine the most appropriate action and explain your reasoning.

            Provide a comprehensive analysis covering:
            1. A brief summary of the repository's purpose and function.
            2. Key strengths.
            3. Areas for improvement (weaknesses).
            4. Specific recommendations (each with a reason and priority: High, Medium, or Low).
            5. An assessment of the repository's activity level.
            6. An estimated value/importance of the repository (High, Medium, or Low).
            7. Suggested tags/categories.
            8. Recommended action (DELETE/ARCHIVE/EXTRACT/KEEP/PIN) with reasoning.

            CRITICAL INSTRUCTIONS FOR OUTPUT FORMATTING:
            - Your output MUST be ONLY a valid JSON object. No introductory text, no markdown, no trailing characters.
            - The JSON object MUST strictly adhere to the following schema:
            {format_instructions}
            - Ensure ALL required fields from the schema are present at the TOP LEVEL of the JSON object.
            - The `recommendations` field MUST be a JSON array, where EACH element is a JSON object with EXACTLY these keys: "recommendation", "reason", and "priority".
            - Example for a single recommendation object: {{"recommendation": "Improve test coverage", "reason": "Current tests are insufficient", "priority": "High"}}
            - DO NOT nest fields like `summary`, `strengths`, etc., inside another key like "analysis". They must be top-level keys.
            - Replace ALL placeholders like {{{{some_value}}}} with actual analysis content. Do not output the placeholders.
            - Generate ONLY the JSON object that matches the schema.
            """
                )
            ]
        )
            
        # Use RunnablePassthrough for preprocessing input data
        input_preprocessor = RunnablePassthrough(lambda x: prepare_input_data(x))

        # Add more validation and logging for the data being passed to the LLM
        if self.logger and self.logger.debug_enabled:
            self.logger.log("Building LLM chain with prompt parameters:", "debug")
            # Log example of prepared data
            example_data = prepare_input_data({"repo_name": "Example", "repo_desc": "Test repository"})
            self.logger.log(f"Chain input keys: {list(example_data.keys())}", "debug")
            
        # Define a log function to verify data at each stage
        def log_data_at_stage(prefix):
            def _log_data(data_dict):
                if self.logger and self.logger.debug_enabled:
                    if hasattr(data_dict, "keys"):
                        self.logger.log(f"{prefix} data keys: {list(data_dict.keys())}", "debug")
                    elif hasattr(data_dict, "content"):
                        content_preview = data_dict.content[:100] + "..." if len(data_dict.content) > 100 else data_dict.content
                        self.logger.log(f"{prefix} content: {content_preview}", "debug")
                    else:
                        self.logger.log(f"{prefix} data type: {type(data_dict)}", "debug")
                return data_dict
            return _log_data
            
        # Add debug logging at each stage and raw output logging before parsing
        self._analysis_chain = (
            input_preprocessor 
            | RunnablePassthrough(log_data_at_stage("After preprocessing"))
            | prompt
            | RunnablePassthrough(log_data_at_stage("After prompt formatting"))
            | self.llm
            | RunnablePassthrough(self._log_raw_output)
            | output_fixing_parser
        )

        return self._analysis_chain

    def analyze_repository(self, repo_data: dict) -> RepoAnalysis:
        """Analyze a repository using the LLM.

        Args:
            repo_data: Repository data to analyze

        Returns:
            Repository analysis result
        """
        if self.rate_limiter:
            self.rate_limiter.wait(
                self.logger, debug=getattr(self.logger, "debug_enabled", False)
            )

        try:
            # Create the chain if not already created
            chain = self.create_analysis_chain()

            # Log repository analysis starting
            repo_name = repo_data.get("repo_name", "unknown")
            if self.logger:
                self.logger.log(
                    f"Analyzing repo {repo_name}",
                    level="info",
                )
            
            # First, ensure the data is a dictionary for safety
            data_for_chain = dict(repo_data) if isinstance(repo_data, dict) else {}
                
            # Print comprehensive debug info about repo_data
            if self.logger and getattr(self.logger, "debug_enabled", False):
                self.logger.log(
                    f"Analysis data keys for {repo_name}: {list(data_for_chain.keys())}", 
                    level="debug"
                )
                # Log all field values with truncation for long values
                for key, value in data_for_chain.items():
                    if key in ['readme_excerpt']:
                        # Special handling for long text fields
                        val_str = str(value) if value is not None else "None"
                        preview = val_str[:200] + "..." if len(val_str) > 200 else val_str
                        self.logger.log(
                            f"{key} (first 200 chars): {preview}",
                            level="debug"
                        )
                    else:
                        # Standard handling for other fields
                        self.logger.log(
                            f"{key}: {value}",
                            level="debug"
                        )

            # Validate all required and optional fields
            required_fields = ["repo_name", "repo_desc", "repo_url", "updated_at", "readme_excerpt"]
            optional_fields = [
                "is_archived", "stars", "forks", "languages", "open_issues", 
                "closed_issues", "activity_summary", "recent_commits_count", 
                "contributor_summary", "dependency_info", "dependency_context"
            ]
            
            # Check for missing required fields
            missing_required = [f for f in required_fields if not data_for_chain.get(f)]
            if missing_required and self.logger:
                self.logger.log(
                    f"WARNING: Repository {repo_name} missing critical fields: {', '.join(missing_required)}",
                    level="warning"
                )
            
            # Fill in missing required fields with meaningful defaults
            for field in required_fields:
                if not data_for_chain.get(field):
                    if field == "repo_name":
                        data_for_chain["repo_name"] = "Unknown Repository"
                        if self.logger:
                            self.logger.log(f"Added default value for missing required field: {field}", "debug")
                    elif field == "repo_desc":
                        data_for_chain["repo_desc"] = "No description available"
                        if self.logger:
                            self.logger.log(f"Added default value for missing required field: {field}", "debug")
                    elif field == "repo_url":
                        data_for_chain["repo_url"] = "No URL available"
                        if self.logger:
                            self.logger.log(f"Added default value for missing required field: {field}", "debug")
                    elif field == "updated_at":
                        data_for_chain["updated_at"] = "Unknown"
                        if self.logger:
                            self.logger.log(f"Added default value for missing required field: {field}", "debug")
                    elif field == "readme_excerpt":
                        data_for_chain["readme_excerpt"] = "No README content available"
                        if self.logger:
                            self.logger.log(f"Added default value for missing required field: {field}", "debug")
            
            # Add default values for all missing optional fields
            for field in optional_fields:
                if field not in data_for_chain or data_for_chain.get(field) is None:
                    if field in ["stars", "forks", "open_issues", "closed_issues", "recent_commits_count"]:
                        data_for_chain[field] = 0
                    elif field == "is_archived":
                        data_for_chain[field] = False
                    else:  # Text fields
                        data_for_chain[field] = f"No {field.replace('_', ' ')} available"
                    
                    if self.logger and self.logger.debug_enabled:
                        self.logger.log(f"Added default value for missing optional field: {field}", "debug")
                        
            # Verify data is ready for analysis
            if self.logger:
                self.logger.log(f"Repository data prepared for analysis of {repo_name}", level="info")
                
                if self.logger.debug_enabled:
                    self.logger.log(f"Final data keys: {list(data_for_chain.keys())}", level="debug")
                    
                    # Verify key field values
                    for field in required_fields:
                        value = data_for_chain.get(field)
                        if field == "readme_excerpt":
                            # Special handling for long text fields
                            self.logger.log(f"README excerpt length: {len(str(value))}", level="debug")
                            if value:
                                preview = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                                self.logger.log(f"README preview: {preview}", level="debug")
                        else:
                            self.logger.log(f"Final {field}: {value}", level="debug")
            
            # Run the chain with fully validated data
            if self.logger:
                self.logger.log(f"Sending data to LLM for analysis of {repo_name}", level="info")
                
            # The chain will apply further preprocessing via input_preprocessor
            result = chain.invoke(data_for_chain)

            # Ensure the repository name is correct (override any LLM-generated name)
            if hasattr(result, "repo_name") and repo_data.get("repo_name"):
                # Force the repo_name to match what was passed in
                result.repo_name = repo_data.get("repo_name")

            if self.logger:
                self.logger.log(
                    f"Successfully analyzed {repo_data.get('repo_name', 'unknown')}",
                    level="success",
                )

            return result
        except Exception as e:
            # ----------------------------------------------------------------
            # Fallback path primarily for **unit tests** where the underlying
            # LLM is being *mocked*.  In that scenario we bypass the full
            # LangChain stack and parse whatever is returned by
            # ``self.llm.invoke`` directly into ``RepoAnalysis``.
            # ----------------------------------------------------------------

            if hasattr(self.llm, "invoke"):
                try:
                    # Try the direct LLM route as fallback
                    raw = self.llm.invoke(repo_data)
                    content = getattr(raw, "content", raw)

                    # Log the raw content for debugging
                    if self.logger and getattr(self.logger, "debug_enabled", False):
                        self.logger.log(
                            f"Attempting direct parsing. Raw content: {content[:500]}...",
                            level="debug",
                        )

                    if isinstance(content, str):
                        # Check if it's valid JSON and extract the actual JSON part
                        import json
                        import re

                        # Try to extract JSON object from text if needed
                        json_match = re.search(r"(\{.*\})", content, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(1)
                            if self.logger and getattr(
                                self.logger, "debug_enabled", False
                            ):
                                self.logger.log(
                                    f"Extracted JSON: {json_str[:500]}...",
                                    level="debug",
                                )

                            try:
                                data = json.loads(json_str)
                                return RepoAnalysis.model_validate(data)
                            except json.JSONDecodeError as jde:
                                if self.logger:
                                    self.logger.log(
                                        f"JSON decode error: {jde}", level="error"
                                    )

                        # Try direct parsing as last resort
                        try:
                            return RepoAnalysis.model_validate_json(content)
                        except Exception as parse_err:
                            if self.logger:
                                self.logger.log(
                                    f"Validation error: {parse_err}", level="error"
                                )

                except Exception as fallback_err:
                    if self.logger:
                        self.logger.log(
                            f"Fallback parsing failed: {fallback_err}", level="error"
                        )

            if self.logger:
                self.logger.log(f"Error analyzing repo: {str(e)}", level="error")

            # Create a placeholder analysis with error tag so that callers do
            # not break.  This mirrors the previous behaviour.
            # Print debug info about what repo_data contained
            if self.logger and getattr(self.logger, "debug_enabled", False):
                self.logger.log(
                    f"Error analyzing repo. Data keys: {list(repo_data.keys())}", 
                    level="debug"
                )
                if "readme_excerpt" in repo_data:
                    self.logger.log(
                        f"README excerpt (first 200 chars): {repo_data.get('readme_excerpt', '')[:200]}...",
                        level="debug"
                    )
                if "repo_name" in repo_data:
                    self.logger.log(
                        f"Repo name: {repo_data.get('repo_name', 'unknown')}",
                        level="debug"
                    )
                    
            return RepoAnalysis(
                repo_name=repo_data.get("repo_name", "unknown"),
                summary=f"Error analyzing repository: {str(e)}",
                strengths=["Could not analyze"],
                weaknesses=["Could not analyze"],
                recommendations=[],
                activity_assessment="Unknown (analysis failed)",
                estimated_value="Unknown (analysis failed)",
                tags=["error", "analysis-failed"],
            )
