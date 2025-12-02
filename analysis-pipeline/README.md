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

