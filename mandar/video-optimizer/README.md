# Video Optimizer Service

Encodes video in multiple resolutions with web-optimized settings for streaming.

## Features
- Multiple resolution outputs (1080p, 720p, 480p)
- Web-optimized MP4 with fast-start for streaming
- Automatic thumbnail generation
- Presigned URLs for direct download
- Quality/size optimized encoding

## Input Format
```json
{
  "session_id": "abc123",
  "input_key": "output/abc123/stitched_abc123_20241128_120000.mp4",
  "resolutions": ["1080p", "720p"],
  "generate_thumbnail": true
}
```

## Output Format
```json
{
  "success": true,
  "data": {
    "session_id": "abc123",
    "input_key": "output/abc123/stitched_abc123_20241128_120000.mp4",
    "input_duration": 45.5,
    "input_resolution": "1920x1080",
    "outputs": [
      {
        "resolution": "1080p",
        "s3_key": "final/abc123/demo_abc123_1080p.mp4",
        "s3_url": "s3://bucket/final/abc123/demo_abc123_1080p.mp4",
        "download_url": "https://presigned-url...",
        "width": 1920,
        "height": 1080,
        "duration": 45.5,
        "file_size": 28500000
      },
      {
        "resolution": "720p",
        "s3_key": "final/abc123/demo_abc123_720p.mp4",
        "s3_url": "s3://bucket/final/abc123/demo_abc123_720p.mp4",
        "download_url": "https://presigned-url...",
        "width": 1280,
        "height": 720,
        "duration": 45.5,
        "file_size": 14200000
      }
    ],
    "thumbnail": {
      "s3_key": "final/abc123/thumbnail.jpg",
      "download_url": "https://presigned-url..."
    },
    "resolutions_generated": 2,
    "completed_at": "2024-11-28T12:05:00.000000"
  }
}
```

## Output Presets
| Preset | Resolution | Video Bitrate | CRF | Audio Bitrate |
|--------|------------|---------------|-----|---------------|
| 1080p | 1920x1080 | 5 Mbps | 23 | 192 kbps |
| 720p | 1280x720 | 2.5 Mbps | 24 | 128 kbps |
| 480p | 854x480 | 1 Mbps | 25 | 96 kbps |

## Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| BUCKET_NAME | S3 bucket name | ai-demo-builder-bucket |
| TABLE_NAME | DynamoDB table | Sessions |
| FFMPEG_PATH | Path to ffmpeg | /opt/bin/ffmpeg |
| FFPROBE_PATH | Path to ffprobe | /opt/bin/ffprobe |

## Local Testing
```bash
python test_local.py
```

## Deployment
```bash
mkdir package
pip install -r requirements.txt -t package/
cp lambda_function.py package/
cd package
zip -r ../video-optimizer.zip .
cd ..

aws lambda create-function \
  --function-name video-optimizer \
  --runtime python3.11 \
  --handler lambda_function.lambda_handler \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-role \
  --zip-file fileb://video-optimizer.zip \
  --timeout 900 \
  --memory-size 3008 \
  --ephemeral-storage Size=10240 \
  --layers arn:aws:lambda:us-east-1:YOUR_ACCOUNT:layer:ffmpeg:1
```

## IAM Permissions Required
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": [
        "arn:aws:s3:::ai-demo-builder-bucket/output/*",
        "arn:aws:s3:::ai-demo-builder-bucket/final/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["dynamodb:UpdateItem"],
      "Resource": "arn:aws:dynamodb:*:*:table/Sessions"
    }
  ]
}
```

## Optimization Features
- **Fast-start**: `movflags +faststart` for web streaming
- **Quality-based encoding**: CRF mode for consistent quality
- **Rate control**: maxrate/bufsize for streaming compatibility
- **Aspect ratio preservation**: Letterboxing for non-16:9 content