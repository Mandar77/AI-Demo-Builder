# AI-Demo-Builder - Person 1 (Xinyu) - Analysis Pipeline

## Overview
This branch contains the Analysis Pipeline implementation by Person 1 (Xinyu), responsible for fetching, parsing, and analyzing GitHub repositories to extract project information.

## Functions

### 1. GitHub Fetcher (`lambda/analysis-pipeline/github-fetcher/`)
- Fetches repository content from GitHub API
- Downloads files and stores them in S3
- Handles authentication and rate limiting

### 2. Content Parser (`lambda/analysis-pipeline/content-parser/`)
- Parses README files and extracts structured information
- Extracts project descriptions, features, and documentation

### 3. Project Analyzer (`lambda/analysis-pipeline/project-analyzer/`)
- Analyzes project structure and architecture
- Detects technology stack, frameworks, and dependencies
- Evaluates project complexity

## File Structure

```
lambda/
├── analysis-pipeline/
│   ├── github-fetcher/          # GitHub repository fetcher
│   ├── content-parser/          # README and content parser
│   └── project-analyzer/         # Project structure analyzer
└── shared/                       # Shared utilities
    ├── s3_utils.py              # S3 operations
    ├── dynamo_utils.py          # DynamoDB operations
    ├── sqs_utils.py             # SQS operations
    └── error_handler.py         # Error handling utilities
```

## Dependencies
- Python 3.9+
- boto3 (AWS SDK)
- PyGithub (GitHub API client)
- markdown, BeautifulSoup (content parsing)

