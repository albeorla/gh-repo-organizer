# Accessing Private GitHub Repositories

This guide explains how to configure the GitHub Repository Organizer to access and analyze both public and private repositories.

## Prerequisites

To access private repositories, you need:

1. A GitHub account with private repositories
2. A GitHub Personal Access Token with appropriate permissions
3. Your GitHub username

## Creating a GitHub Personal Access Token

1. **Go to GitHub Settings**:
   - Log in to GitHub
   - Click on your profile icon in the top-right corner
   - Select "Settings"

2. **Navigate to Developer Settings**:
   - Scroll down to the bottom of the sidebar menu
   - Click on "Developer settings"

3. **Generate a Personal Access Token (PAT)**:
   - Click on "Personal access tokens" → "Tokens (classic)"
   - Click "Generate new token" → "Generate new token (classic)"
   - Enter a descriptive name (e.g., "GitHub Repository Organizer")
   - Set an expiration date (recommended: 90 days)
   - Select the following scopes:
     - `repo` (Full control of private repositories)
       - This includes all repo sub-scopes
   - Click "Generate token"

4. **Save Your Token**:
   - **IMPORTANT**: Copy your token immediately! GitHub only shows it once.
   - Store it securely (e.g., in a password manager)

## Configuring the Repository Organizer

You have two options for providing your GitHub token and username:

### Option 1: Environment Variables (Recommended)

Set the following environment variables:

```bash
# Set environment variables in your shell
export GITHUB_TOKEN=your-github-token
export GITHUB_USERNAME=your-github-username

# Then run the tool
poetry run repo analyze
```

To make these settings persistent, add them to your shell profile file (`.bashrc`, `.zshrc`, etc.).

### Option 2: Using .env File

Create a `.env` file in the project root directory:

```bash
# Create .env file
echo "GITHUB_TOKEN=your-github-token" > .env
echo "GITHUB_USERNAME=your-github-username" >> .env
```

The tool will automatically load settings from this file.

## Testing Access to Private Repositories

To verify your token is working correctly, you can use the included test script:

```bash
# Run the repository fetching test script
poetry run python -m scripts.fetch_all_repos --username your-github-username --verbose
```

This script will show you:
- Total repositories found
- Number of public repositories
- Number of private repositories
- A list of all repositories with their privacy status

## Troubleshooting

If you're having trouble accessing private repositories:

1. **Check Token Scopes**:
   ```bash
   curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
   ```
   Look for `"scopes": ["repo",...]` in the response headers.

2. **Verify Environment Variables**:
   ```bash
   echo $GITHUB_TOKEN
   echo $GITHUB_USERNAME
   ```
   
3. **Common Issues**:
   - Token expired: Create a new token on GitHub
   - Insufficient permissions: Ensure the token has the `repo` scope
   - Incorrect username: Check your GitHub username
   - Rate limiting: The GitHub API has rate limits (60 requests/hour for unauthenticated requests, 5,000/hour for authenticated)

## Security Considerations

- **Never commit your GitHub token to version control**
- Consider using a token with the minimum necessary permissions
- Set a reasonable expiration date for your token
- Revoke tokens when no longer needed

## Related Documentation

- [GitHub API Documentation](https://docs.github.com/en/rest/overview/authenticating-to-the-rest-api)
- [Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [GitHub Rate Limiting](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting)