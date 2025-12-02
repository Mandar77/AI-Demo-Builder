# Service 4: Cache Service

This service manages DynamoDB cache for storing and retrieving cached data.

## File Structure

- `cache_service.py`: Main service logic and Lambda handler function
- `test_local.py`: Local testing script
- `requirements.txt`: Python dependencies (boto3)

**Note**: The Lambda handler function is directly in `cache_service.py`. When deploying to AWS Lambda, set the handler to: `cache_service.lambda_handler`

## Features

- Get cached items by key
- Set cache items with optional TTL
- Delete cache items
- Supports DynamoDB table configuration
- Comprehensive error handling

## Input Format

### Get Operation

```json
{
  "operation": "get",
  "key": "github_facebook_react"
}
```

### Set Operation

```json
{
  "operation": "set",
  "key": "github_facebook_react",
  "value": {"projectName": "react", "stars": 200000},
  "ttl": 3600
}
```

### Delete Operation

```json
{
  "operation": "delete",
  "key": "github_facebook_react"
}
```

## Output Format

### Get Operation - Success (200)

```json
{
  "statusCode": 200,
  "body": {
    "found": true,
    "value": {"projectName": "react", "stars": 200000}
  }
}
```

```json
{
  "statusCode": 200,
  "body": {
    "found": false,
    "value": null
  }
}
```

### Set/Delete Operation - Success (200)

```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "key": "github_facebook_react"
  }
}
```

### Error (400, 500, 503)

```json
{
  "statusCode": 400,
  "body": {
    "error": "Missing required field: key"
  }
}
```

## Environment Variables

- `DYNAMODB_TABLE`: DynamoDB table name (default: `ai-demo-cache`)

## DynamoDB Table Schema

The DynamoDB table should have the following structure:

- **Table Name**: `ai-demo-cache` (or value of `DYNAMODB_TABLE`)
- **Primary Key**: `cacheKey` (String)
- **Optional**: `ttl` attribute (Number) for automatic expiration

### Creating the Table

```bash
aws dynamodb create-table \
  --table-name ai-demo-cache \
  --attribute-definitions AttributeName=cacheKey,AttributeType=S \
  --key-schema AttributeName=cacheKey,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### Setting up TTL (Optional)

```bash
aws dynamodb update-time-to-live \
  --table-name ai-demo-cache \
  --time-to-live-specification Enabled=true,AttributeName=ttl
```

## Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Option 1: Use DynamoDB Local
# Download and run DynamoDB Local, then set endpoint:
export AWS_ENDPOINT_URL=http://localhost:8000

# Option 2: Mock boto3 for unit tests
# Use moto library for mocking

# Run tests
python test_local.py
```

## Deployment

Package and deploy to AWS Lambda:

```bash
# Install dependencies in a directory
mkdir package
pip install -r requirements.txt -t package/

# Copy service files
cp cache_service.py package/

# Create deployment package
cd package
zip -r ../service4-cache-service.zip .
cd ..

# Upload to Lambda (via AWS CLI or console)
# IMPORTANT: Set the Lambda handler to: cache_service.lambda_handler
```

## IAM Permissions

The Lambda function needs the following IAM permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/ai-demo-cache"
    }
  ]
}
```

## Error Codes

- `400`: Invalid input (missing or invalid fields)
- `500`: Internal server error
- `503`: Service unavailable (DynamoDB table not found)

## Dependencies

- `boto3`: AWS SDK for Python (for DynamoDB operations)

## Operations

- **get**: Retrieve cached value by key
- **set**: Store value in cache with optional TTL
- **delete**: Remove cached item by key

