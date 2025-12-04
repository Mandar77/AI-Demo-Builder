# Person 4 CDK Stack - Video Processing Services

This CDK stack deploys all 5 Lambda functions for Person 4's video processing pipeline.

## Services Deployed

| Service # | Name | Lambda Name |
|-----------|------|-------------|
| 11 | Job Queue Service | job-queue-manager |
| 12 | Slide Creator | slide-generator |
| 13 | Video Stitcher | video-stitcher |
| 14 | Video Optimizer | video-optimizer |
| 15 | Public Link Generator | public-link-generator |

## Prerequisites

1. AWS CLI configured with credentials
2. Node.js 18+
3. CDK CLI installed globally: `npm install -g aws-cdk`
4. FFmpeg Lambda Layer ARN from Sampada

## Setup

```bash
cd mandar/cdk
npm install
```

## Before Deploying

**IMPORTANT:** Update the FFmpeg Layer ARN in `lib/video-processing-stack.ts`:

```typescript
const ffmpegLayerArn = 'arn:aws:lambda:us-east-1:YOUR_ACCOUNT:layer:ffmpeg-layer:1';
```

## Deploy

```bash
# First time only - bootstrap CDK
cdk bootstrap

# Preview changes
cdk diff

# Deploy
cdk deploy
```

## Useful Commands

| Command | Description |
|---------|-------------|
| `cdk synth` | Generate CloudFormation template |
| `cdk diff` | Compare with deployed stack |
| `cdk deploy` | Deploy the stack |
| `cdk destroy` | Delete all resources |

## Resources Created

- **SQS Queue**: video-processing-jobs
- **Lambda Functions**: 5 functions with appropriate permissions
- **IAM Roles**: Auto-generated with least-privilege permissions

## Notes

- S3 bucket and DynamoDB table are referenced (not created) since they're shared with other team members
- FFmpeg layer is referenced from Sampada's deployment
- All Lambda permissions are automatically configured