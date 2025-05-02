# Claude Code Project Guide

This document provides actionable guidelines for:
- Using [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview) as your agentic coding tool
- Setting up, configuring, and maintaining your project with Claude Code
- Creating, maintaining, and evolving rules and workflows for effective AI-assisted development
- Ensuring security, clarity, and continuous improvement across the codebase

## 1. Claude Code Overview

[Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview) is an agentic coding tool by Anthropic that operates directly in your terminal, understands your codebase, and helps you code faster through natural language commands. It streamlines your workflow without requiring additional servers or complex setup.

### Key Capabilities
- Editing files and fixing bugs across your codebase
- Answering questions about your code's architecture and logic
- Executing and fixing tests, linting, and other commands
- Searching through git history, resolving merge conflicts, and creating commits and PRs
- Automating CI and infra workflows (non-interactive mode)

### Security and Privacy
- Direct API connection to Anthropic (no intermediate servers)
- Operates in your terminal, maintaining project context
- Strict privacy safeguards and limited data retention ([see docs](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview#security-and-privacy-by-design))

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

## 4. CLI Commands and Usage Patterns

Claude Code provides a rich CLI for interactive and non-interactive use. See the [official CLI command reference](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview#cli-commands).

| Command                       | Description                              | Example                                                                                                 |
| ----------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| claude                        | Start interactive REPL                   | claude                                                                                                  |
| claude "query"                | Start REPL with initial prompt           | claude "how does our authentication system work?"                                                      |
| claude commit                 | Create a commit                          | claude commit                                                                                           |
| claude -p "<command>"         | Non-interactive mode (for CI/scripts)    | claude -p "update the README with the latest changes"                                                  |

For more, see [Claude Code Tutorials](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/tutorials).

## 5. Environment Variables and Configuration

- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
- `CLAUDE_CODE_USE_BEDROCK=1`: Use Amazon Bedrock as backend ([see docs](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview#connect-to-amazon-bedrock))
- `CLAUDE_CODE_USE_VERTEX=1`: Use Google Vertex AI as backend ([see docs](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview#connect-to-google-vertex-ai))
- `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_CUSTOM_HEADERS`, `HTTP_PROXY`, `HTTPS_PROXY`: Proxy and custom header support
- For full configuration options, see [Claude Code Configuration](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview#environment-variables) 