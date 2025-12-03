# Slide Generator Service

Generates PNG transition slides for demo videos using Node.js Canvas.

## Features
- Creates professional-looking slides with gradients and decorations
- Three slide types: `title`, `section`, `end`
- Uploads directly to S3
- Updates DynamoDB session with slide metadata

## Input Format
```json
{
  "session_id": "abc123",
  "slides": [
    {
      "id": "intro",
      "type": "title",
      "order": 0,
      "content": {
        "title": "My Project Demo",
        "subtitle": "A quick walkthrough",
        "projectName": "MyProject"
      }
    },
    {
      "id": "section1",
      "type": "section",
      "order": 1,
      "content": {
        "sectionNumber": 1,
        "sectionTitle": "Installation",
        "sectionDescription": "Setting up the project"
      }
    },
    {
      "id": "outro",
      "type": "end",
      "order": 5,
      "content": {
        "projectName": "MyProject",
        "githubUrl": "https://github.com/user/repo",
        "message": "Thank You!"
      }
    }
  ]
}
```

## Output Format
```json
{
  "success": true,
  "data": {
    "session_id": "abc123",
    "slides_generated": 3,
    "slides": [
      {
        "id": "intro",
        "type": "title",
        "order": 0,
        "s3_key": "slides/abc123/intro.png",
        "s3_url": "s3://ai-demo-builder-bucket/slides/abc123/intro.png",
        "created_at": "2024-11-28T10:00:00.000Z"
      }
    ]
  }
}
```

## Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| BUCKET_NAME | S3 bucket name | ai-demo-builder-bucket |
| TABLE_NAME | DynamoDB table name | Sessions |
| AWS_REGION | AWS region | us-east-1 |

## Local Testing
```bash
npm install
npm test
```
This generates sample slides in the `test_output/` directory.

## Deployment
```bash
# Install dependencies
npm install

# Create deployment package
zip -r slide-generator.zip index.js node_modules package.json

# Deploy to Lambda (using AWS CLI)
aws lambda create-function \
  --function-name slide-generator \
  --runtime nodejs18.x \
  --handler index.handler \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-role \
  --zip-file fileb://slide-generator.zip \
  --timeout 60 \
  --memory-size 1024

# Or update existing function
aws lambda update-function-code \
  --function-name slide-generator \
  --zip-file fileb://slide-generator.zip
```

## IAM Permissions Required
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject"],
      "Resource": "arn:aws:s3:::ai-demo-builder-bucket/slides/*"
    },
    {
      "Effect": "Allow",
      "Action": ["dynamodb:UpdateItem"],
      "Resource": "arn:aws:dynamodb:*:*:table/Sessions"
    }
  ]
}
```