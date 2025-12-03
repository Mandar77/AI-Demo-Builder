# Job Queue Manager Service

Manages SQS job queue for video processing pipeline with prioritization and status tracking.

## Features
- Submit jobs to SQS queue with priority levels
- Process jobs (can be triggered by SQS or manually)
- Track job status in DynamoDB
- Orchestrate full video processing pipeline
- Get queue statistics

## Operations

### Submit Job
```json
{
  "operation": "submit",
  "session_id": "abc123",
  "job_type": "full_pipeline",
  "priority": 5,
  "payload": {
    "videos": ["video1.mp4", "video2.mp4"],
    "slides": ["intro.png", "section1.png"]
  }
}
```

### Check Job Status
```json
{
  "operation": "status",
  "session_id": "abc123"
}
```

### Get Queue Stats
```json
{
  "operation": "stats"
}
```

### Process Jobs (Manual)
```json
{
  "operation": "process",
  "max_jobs": 5
}
```

## Job Types
| Type | Description |
|------|-------------|
| `stitch_video` | Concatenate videos and slides |
| `optimize_video` | Encode video in multiple resolutions |
| `generate_slides` | Create transition slides |
| `full_pipeline` | Run complete processing pipeline |

## Priority Levels
| Level | Value | Description |
|-------|-------|-------------|
| HIGH | 1 | Process immediately |
| NORMAL | 5 | Standard processing |
| LOW | 10 | Process when queue is empty |

## Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| QUEUE_URL | SQS queue URL | Required |
| TABLE_NAME | DynamoDB table | Sessions |
| VIDEO_STITCHER_FUNCTION | Stitcher Lambda name | video-stitcher |
| VIDEO_OPTIMIZER_FUNCTION | Optimizer Lambda name | video-optimizer |
| MAX_CONCURRENT_JOBS | Max parallel jobs | 3 |
| JOB_TIMEOUT_MINUTES | Job timeout | 15 |

## Deployment
```bash
npm install
zip -r job-queue-manager.zip index.js node_modules package.json

aws lambda create-function \
  --function-name job-queue-manager \
  --runtime nodejs18.x \
  --handler index.handler \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-role \
  --zip-file fileb://job-queue-manager.zip \
  --timeout 300 \
  --memory-size 512 \
  --environment Variables="{QUEUE_URL=https://sqs.us-east-1.amazonaws.com/XXX/video-jobs}"
```

## SQS Queue Setup
```bash
aws sqs create-queue \
  --queue-name video-processing-jobs \
  --attributes VisibilityTimeout=900,MessageRetentionPeriod=86400
```

## IAM Permissions Required
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      "Resource": "arn:aws:sqs:*:*:video-processing-jobs"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/Sessions"
    },
    {
      "Effect": "Allow",
      "Action": ["lambda:InvokeFunction"],
      "Resource": [
        "arn:aws:lambda:*:*:function:video-stitcher",
        "arn:aws:lambda:*:*:function:video-optimizer"
      ]
    }
  ]
}
```