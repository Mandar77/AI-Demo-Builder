# Service 2: README Parser

This service parses README content and extracts structured information.

## File Structure

- `readme_parser.py`: Main service logic and Lambda handler function
- `test_local.py`: Local testing script
- `requirements.txt`: Python dependencies (empty - uses standard library only)

**Note**: The Lambda handler function is directly in `readme_parser.py`. When deploying to AWS Lambda, set the handler to: `readme_parser.lambda_handler`

## Features

- Extracts title from README (first H1 heading)
- Parses features list from Features section
- Extracts installation instructions
- Extracts usage examples
- Determines if README has substantial documentation
- Uses only Python standard library (no external dependencies)

## Input Format

```json
{
  "readme": "# Project\n## Features\n- Feature 1\n- Feature 2"
}
```

## Output Format

### Success (200)

```json
{
  "statusCode": 200,
  "body": {
    "title": "Project",
    "features": ["Feature 1", "Feature 2"],
    "installation": "npm install ...",
    "usage": "...",
    "hasDocumentation": true
  }
}
```

### Error (500)

```json
{
  "statusCode": 500,
  "body": {
    "error": "Error message"
  }
}
```

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
zip -r service2-readme-parser.zip readme_parser.py

# Upload to Lambda (via AWS CLI or console)
# IMPORTANT: Set the Lambda handler to: readme_parser.lambda_handler
```

## Dependencies

- None (uses Python standard library only: `re`, `json`)

## Parsing Logic

- **Title**: Extracted from first H1 heading (`# Title`)
- **Features**: Extracted from Features section bullet lists
- **Installation**: Extracted from Installation/Install section
- **Usage**: Extracted from Usage section
- **Documentation Check**: True if README has multiple sections, code blocks, or links

