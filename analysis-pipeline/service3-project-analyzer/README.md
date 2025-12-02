# Service 3: Project Analyzer

This service analyzes project type and complexity based on GitHub repository data and parsed README content.

## File Structure

- `project_analyzer.py`: Main service logic and Lambda handler function
- `test_local.py`: Local testing script
- `requirements.txt`: Python dependencies (empty - uses standard library only)

**Note**: The Lambda handler function is directly in `project_analyzer.py`. When deploying to AWS Lambda, set the handler to: `project_analyzer.lambda_handler`

## Features

- Determines project type (library, framework, application, CLI tool, etc.)
- Assesses project complexity (low, medium, high)
- Extracts technology stack information
- Identifies key features
- Suggests number of segments for project breakdown

## Input Format

```json
{
  "github_data": {
    "stars": 200000,
    "language": "JavaScript",
    "topics": ["ui", "frontend"]
  },
  "parsed_readme": {
    "features": ["Virtual DOM"],
    "hasDocumentation": true
  }
}
```

## Output Format

### Success (200)

```json
{
  "statusCode": 200,
  "body": {
    "projectType": "library",
    "complexity": "high",
    "techStack": ["React", "JavaScript"],
    "keyFeatures": ["Virtual DOM"],
    "suggestedSegments": 5
  }
}
```

### Error (400, 500)

```json
{
  "statusCode": 400,
  "body": {
    "error": "Missing required field: github_data"
  }
}
```

## Project Types

- `framework`: UI or application frameworks
- `library`: Code libraries and SDKs
- `application`: Full applications
- `cli-tool`: Command-line utilities
- `plugin`: Plugins and extensions
- `unknown`: Could not determine

## Complexity Levels

- `low`: Small projects with few features
- `medium`: Moderate complexity projects
- `high`: Large, complex projects with many features

## Local Testing

```bash
# No dependencies to install - uses standard library only

# Run tests
python test_local.py
```

## Deployment

Package and deploy to AWS Lambda:

```bash
# Create deployment package (include all Python files)
zip -r service3-project-analyzer.zip project_analyzer.py

# Upload to Lambda (via AWS CLI or console)
# IMPORTANT: Set the Lambda handler to: project_analyzer.lambda_handler
```

## Dependencies

- None (uses Python standard library only)

## Analysis Logic

- **Project Type**: Determined from topics, language, and README keywords
- **Complexity**: Based on stars, feature count, documentation quality
- **Tech Stack**: Extracted from language, topics, and README features
- **Key Features**: First 5 features from parsed README
- **Suggested Segments**: Calculated from complexity and project type (1-10)

