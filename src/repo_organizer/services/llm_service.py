"""
Language model service for analyzing repository content.

This module implements the Strategy pattern for the language model service,
allowing different LLM backends to be used with a consistent interface.
"""

from typing import Any, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain.output_parsers import OutputFixingParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from repo_organizer.models.repo_models import RepoAnalysis
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
        model_name: str = "claude-3-opus-20240229",
        rate_limiter: Optional[RateLimiter] = None,
        logger: Optional[Logger] = None,
    ):
        """Initialize the LLM service.

        Args:
            api_key: API key for the language model provider
            model_name: Model name to use
            rate_limiter: Optional rate limiter for API calls
            logger: Optional logger for service operations
        """
        self.api_key = api_key
        self.model_name = model_name
        self.rate_limiter = rate_limiter
        self.logger = logger
        self.llm = ChatAnthropic(
            model=model_name,
            temperature=0.2,
            anthropic_api_key=api_key,
            max_retries=3,  # Built-in retries for LangChain
        )

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

        # Create the prompt template using modern ChatPromptTemplate
        prompt = ChatPromptTemplate.from_messages(
            [
                HumanMessage(
                    content="""
            Analyze the GitHub repository based on the provided information. This is YOUR OWN personal repository, not a public library.

            Repository Information:
            - Name: {repo_name}
            - Description: {repo_desc}
            - URL: {repo_url}
            - Last Updated: {updated_at}
            - Archived on GitHub: {is_archived}
            - Stars: {stars}
            - Forks: {forks}
            - Programming Languages: {languages}
            
            Provide a comprehensive analysis covering:
            1. A brief summary of the repository's purpose and function (focus on it being YOUR OWN personal project, not a public library).
            2. Key strengths.
            3. Areas for improvement (weaknesses).
            4. Specific recommendations (each with a reason and priority: High, Medium, or Low).
            5. An assessment of the repository's activity level.
            6. An estimated value/importance of the repository to YOU (High, Medium, or Low).
            7. Suggested tags/categories.
            
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

        # Create the LCEL chain using modern pattern with fixed format instructions
        chain_input = {
            "repo_name": lambda x: x["repo_name"],
            "repo_desc": lambda x: x["repo_desc"],
            "repo_url": lambda x: x["repo_url"],
            "updated_at": lambda x: x["updated_at"],
            "is_archived": lambda x: x["is_archived"],
            "stars": lambda x: x["stars"],
            "forks": lambda x: x["forks"],
            "languages": lambda x: x["languages"],
            "format_instructions": lambda _: pydantic_parser.get_format_instructions(),  # Use base parser instructions
        }

        # Add raw output logging step before the OutputFixingParser
        self._analysis_chain = (
            chain_input
            | prompt
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

            # Run the chain
            if self.logger:
                self.logger.log(
                    f"Analyzing repo {repo_data.get('repo_name', 'unknown')}",
                    level="info",
                )

            result = chain.invoke(repo_data)

            if self.logger:
                self.logger.log(
                    f"Successfully analyzed {repo_data.get('repo_name', 'unknown')}",
                    level="success",
                )

            return result
        except Exception as e:
            if self.logger:
                self.logger.log(f"Error analyzing repo: {str(e)}", level="error")

            # Create a placeholder analysis with error tag
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
