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
- Orchestrates Service 2 (README Parser) and Service 3 (Project Analyzer)
- Implements caching for improved performance (cache hit/miss handling)
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

The service returns aggregated results from Service 1, Service 2, and Service 3:

```json
{
  "statusCode": 200,
  "body": {
    "github_data": {
      "projectName": "react",
      "owner": "facebook",
      "stars": 200000,
      "language": "JavaScript",
      "topics": ["ui", "frontend"],
      "description": "The library for web and native user interfaces",
      "readme": "# React\n..."
    },
    "parsed_readme": {
      "title": "React",
      "features": ["Declarative", "Component-Based"],
      "installation": "...",
      "usage": "...",
      "hasDocumentation": true
    },
    "project_analysis": {
      "projectType": "framework",
      "complexity": "high",
      "techStack": ["JavaScript", "React"],
      "keyFeatures": [...],
      "suggestedSegments": 8
    }
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

## Workflow

1. **Check Cache**: First checks if the repository analysis is already cached
   - If cache hit: Returns cached result immediately (fast response)
   - If cache miss: Proceeds with computation

2. **Fetch GitHub Data**: Retrieves repository metadata and README content

3. **Call Service 2**: Parses README content for structured information

4. **Call Service 3**: Analyzes project type, complexity, and tech stack

5. **Cache Results**: Stores the complete analysis in DynamoDB cache for future requests

6. **Return Results**: Returns aggregated data to the caller

## Caching

The service implements caching using Service 4 (Cache Service) to improve performance:

- **Cache Key Format**: `github_{owner}_{projectName}`
- **Cache TTL**: 3600 seconds (1 hour) by default
- **Cache Operations**: 
  - Read: Checks cache before computation (cache hit returns immediately)
  - Write: Stores results after computation for future requests

## Environment Variables

- `GITHUB_API`: GitHub API base URL (default: `https://api.github.com`)
- `GITHUB_TOKEN`: GitHub personal access token (optional, but recommended)
- `DYNAMODB_TABLE`: DynamoDB cache table name (default: `ai-demo-cache`)

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

## Service Integration

This service orchestrates multiple Lambda functions:

- **Service 2** (`service2-readme-parser`): Parses README content
- **Service 3** (`service3-project-analyzer`): Analyzes project structure
- **Service 4** (`service4-cache-service`): Manages caching in DynamoDB

## Dependencies

- `requests`: For HTTP requests to GitHub API
- `boto3`: For AWS Lambda-to-Lambda invocation and DynamoDB access

