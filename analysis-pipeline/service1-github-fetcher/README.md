# Service 1: GitHub Repository Fetcher

This service fetches GitHub repository information and README content.

## File Structure

- `github_fetcher.py`: Main service logic and Lambda handler function
- `config.py`: Configuration and environment variables
- `test_local.py`: Local testing script
- `requirements.txt`: Python dependencies

**Note**: The Lambda handler function is directly in `github_fetcher.py`. When deploying to AWS Lambda, set the handler to: `github_fetcher.lambda_handler`

## Features

- Fetches repository metadata (name, owner, stars, language, topics, description)
- Retrieves README content from the repository
- Handles various GitHub URL formats
- Supports GitHub personal access token for rate limit increases
- Comprehensive error handling

## Input Format

```json
{
  "github_url": "https://github.com/facebook/react"
}
```

## Output Format

### Success (200)

```json
{
  "statusCode": 200,
  "body": {
    "projectName": "react",
    "owner": "facebook",
    "stars": 200000,
    "language": "JavaScript",
    "topics": ["ui", "frontend"],
    "description": "The library for web and native user interfaces",
    "readme": "# React\n..."
  }
}
```

### Error (400, 401, 403, 404, 500)

```json
{
  "statusCode": 404,
  "body": {
    "error": "Repository not found"
  }
}
```

## Environment Variables

- `GITHUB_API`: GitHub API base URL (default: `https://api.github.com`)
- `GITHUB_TOKEN`: GitHub personal access token (optional, but recommended)

## Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python test_local.py
```

## Deployment

Package and deploy to AWS Lambda:

```bash
# Create deployment package (include all Python files)
zip -r service1-github-fetcher.zip github_fetcher.py config.py

# Install dependencies
pip install -r requirements.txt -t .

# Add dependencies to package
zip -r service1-github-fetcher.zip . -x "*.pyc" "__pycache__/*" "*.zip"

# Upload to Lambda (via AWS CLI or console)
# IMPORTANT: Set the Lambda handler to: github_fetcher.lambda_handler
```

## Error Codes

- `400`: Invalid input (missing or malformed github_url)
- `401`: Invalid or missing GitHub token
- `403`: Rate limit exceeded or access forbidden
- `404`: Repository not found
- `500`: Internal server error

## Dependencies

- `requests`: For HTTP requests to GitHub API

