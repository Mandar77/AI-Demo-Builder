## Services Overview

### Service 1: GitHub Repository Fetcher
- **Purpose**: Fetches GitHub repository information and README content
- **Input**: GitHub URL
- **Output**: Repository metadata + README text
- **Dependencies**: `requests`

### Service 2: README Parser
- **Purpose**: Parses README content and extracts structured information
- **Input**: README text (from Service 1)
- **Output**: Structured README data (title, features, installation, usage)
- **Dependencies**: None (Python standard library only)

### Service 3: Project Analyzer
- **Purpose**: Analyzes project type and complexity
- **Input**: GitHub data (Service 1) + Parsed README (Service 2)
- **Output**: Project analysis (type, complexity, tech stack, suggested segments)
- **Dependencies**: None (Python standard library only)

### Service 4: Cache Service
- **Purpose**: Manages DynamoDB cache for storing and retrieving cached data
- **Input**: Operation (get/set/delete) + key + optional value
- **Output**: Cached data or operation status
- **Dependencies**: `boto3`

## Project Structure

```
my-services/
├── service1-github-fetcher/          # Service 1: GitHub Fetcher
│   ├── github_fetcher.py            # Main service logic + Lambda handler
│   ├── config.py
│   ├── requirements.txt
│   ├── test_local.py
│   └── README.md
│
├── service2-readme-parser/           # Service 2: README Parser
│   ├── readme_parser.py             # Main service logic + Lambda handler
│   ├── requirements.txt
│   ├── test_local.py
│   └── README.md
│
├── service3-project-analyzer/        # Service 3: Project Analyzer
│   ├── project_analyzer.py          # Main service logic + Lambda handler
│   ├── requirements.txt
│   ├── test_local.py
│   └── README.md
│
├── service4-cache-service/           # Service 4: Cache Service
│   ├── cache_service.py             # Main service logic + Lambda handler
│   ├── requirements.txt
│   ├── test_local.py
│   └── README.md
│
├── mock_data/                        # Test data (optional)
│   └── .gitkeep
│
└── README.md                         # This file
```

## Design Principles

✅ **Each service is completely independent**
- Own folder with all necessary files
- Own dependencies (requirements.txt)
- No cross-service imports

✅ **Uniform interface standard**
- All services use same Lambda handler signature
- Standard response format: `{"statusCode": 200, "body": {...}}`
- Consistent error handling

✅ **Zero dependency conflicts**
- Each service manages its own dependencies
- No shared code between services
- Easy to merge with other team members' services

✅ **Easy to integrate**
- API Gateway endpoint for frontend integration
- Documented input/output formats in API_GATEWAY_INFO_EN.md
- Services can be called independently or chained together

## Quick Start

### Local Testing

Each service can be tested independently:

```bash
# Service 1
cd service1-github-fetcher
pip install -r requirements.txt
python test_local.py

# Service 2
cd service2-readme-parser
python test_local.py  # No dependencies needed

# Service 3
cd service3-project-analyzer
python test_local.py  # No dependencies needed

# Service 4
cd service4-cache-service
pip install -r requirements.txt
# Note: Requires DynamoDB or mocking for full testing
python test_local.py
```

### Deployment

Each service is deployed independently to AWS Lambda:

```bash
# Example: Deploy Service 1
cd service1-github-fetcher
zip -r ../service1-github-fetcher.zip github_fetcher.py config.py
pip install -r requirements.txt -t .
zip -r ../service1-github-fetcher.zip . -x "*.pyc" "__pycache__/*"

# Upload to Lambda via AWS CLI or Console
# IMPORTANT: Set Handler to: github_fetcher.lambda_handler
```

**Lambda Handler Configuration**:
Each service has its handler function directly in the main Python file. When creating/updating the Lambda function, set the handler to:
- Service 1: `github_fetcher.lambda_handler`
- Service 2: `readme_parser.lambda_handler`
- Service 3: `project_analyzer.lambda_handler`
- Service 4: `cache_service.lambda_handler`

In AWS Lambda Console: Go to Configuration → General → Edit → Handler field

## Service Integration Flow

```
1. Service 1: Fetch GitHub data
   Input:  {"github_url": "https://github.com/..."}
   Output: {projectName, owner, stars, language, readme, ...}

2. Service 2: Parse README
   Input:  {"readme": "..."}
   Output: {title, features, installation, usage, hasDocumentation}

3. Service 3: Analyze project
   Input:  {
     "github_data": {...},      // from Service 1
     "parsed_readme": {...}     // from Service 2
   }
   Output: {projectType, complexity, techStack, suggestedSegments}

4. Service 4: Cache results (optional)
   Input:  {"operation": "set", "key": "...", "value": {...}}
   Output: {"success": true}
```

## API Documentation

API Gateway endpoint documentation is available in [API_GATEWAY_INFO_EN.md](./API_GATEWAY_INFO_EN.md).

This document includes:
- API endpoint and request format
- Response format with all fields
- Usage examples (JavaScript, Python, curl)
- Error handling
- CORS configuration

## Environment Variables

### Service 1
- `GITHUB_API`: GitHub API base URL (default: `https://api.github.com`)
- `GITHUB_TOKEN`: GitHub personal access token (optional)

### Service 4
- `DYNAMODB_TABLE`: DynamoDB table name (default: `ai-demo-cache`)

## Team Integration

This structure is designed for easy integration with other team members' services:

- **No conflicts**: Each person works in their own folder
- **Clear interfaces**: API Gateway endpoint documented for frontend integration
- **Independent deployment**: Each service deployed separately
- **Easy merging**: Simply combine folders when ready

### Example Team Structure

```
final-repo/
├── person1-services/           # My services
│   ├── service1-github-fetcher/
│   ├── service2-readme-parser/
│   ├── service3-project-analyzer/
│   └── service4-cache-service/
│
├── person2-services/           # Person 2's services
│   └── service5-...
│
└── person3-services/           # Person 3's services
    └── service6-...
```

## Error Handling

All services follow a consistent error handling pattern:

- **200**: Success
- **400**: Bad Request (invalid input)
- **401**: Unauthorized (Service 1 - GitHub token)
- **403**: Forbidden (Service 1 - Rate limit)
- **404**: Not Found (Service 1 - Repository)
- **500**: Internal Server Error
- **503**: Service Unavailable (Service 4 - DynamoDB table not found)

## Testing

Each service includes a `test_local.py` script for local testing without AWS Lambda environment:

```bash
cd service1-github-fetcher
python test_local.py
```

## Dependencies Summary

| Service | Dependencies |
|---------|--------------|
| Service 1 | `requests==2.31.0` |
| Service 2 | None (standard library) |
| Service 3 | None (standard library) |
| Service 4 | `boto3==1.34.0` |

## Notes

- All code comments and documentation are in English
- Each service is self-contained and can be moved/copied independently
- Lambda handlers follow AWS Lambda Python runtime conventions
- Services can be chained together or called independently

## License

This is part of a team project. Each service is designed to be independent and easily integrated.

