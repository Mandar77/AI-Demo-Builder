# Video Stitcher Service

Concatenates multiple video clips and slide images into a single demo video using FFmpeg.

## Features
- Accepts mixed media (videos + slide images)
- Converts slides to video clips with configurable duration
- Normalizes all videos to standard format (1080p, 30fps)
- Adds silent audio tracks where needed
- Concatenates in specified order
- Uploads final video to S3

## Prerequisites
- FFmpeg Lambda Layer (use existing from `sampada/ffmpeg-layer/`)
- S3 bucket for input/output
- DynamoDB Sessions table

## Input Format

### Option 1: Media Items Array
```json
{
  "session_id": "abc123",
  "media_items": [
    {"type": "slide", "key": "slides/abc123/intro.png", "order": 0, "duration": 3},
    {"type": "video", "key": "videos/abc123/video_1.mp4", "order": 10},
    {"type": "slide", "key": "slides/abc123/section1.png", "order": 15, "duration": 2},
    {"type": "video", "key": "videos/abc123/video_2.mp4", "order": 20},
    {"type": "slide", "key": "slides/abc123/end.png", "order": 30, "duration": 3}
  ]
}
```

### Option 2: Separate Videos and Slides
```json
{
  "session_id": "abc123",
  "videos": [
    {"key": "videos/abc123/video_1.mp4", "order": 10},
    {"key": "videos/abc123/video_2.mp4", "order": 20}
  ],
  "slides": [
    {"key": "slides/abc123/intro.png", "order": 0},
    {"key": "slides/abc123/section1.png", "order": 15}
  ]
}
```

## Output Format
```json
{
  "success": true,
  "data": {
    "session_id": "abc123",
    "output_key": "output/abc123/stitched_abc123_20241128_120000.mp4",
    "output_url": "s3://ai-demo-builder-bucket/output/abc123/stitched_abc123_20241128_120000.mp4",
    "duration": 45.5,
    "resolution": "1920x1080",
    "items_processed": 5,
    "created_at": "2024-11-28T12:00:00.000000"
  }
}
```

## Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| BUCKET_NAME | S3 bucket name | ai-demo-builder-bucket |
| TABLE_NAME | DynamoDB table | Sessions |
| FFMPEG_PATH | Path to ffmpeg binary | /opt/bin/ffmpeg |
| FFPROBE_PATH | Path to ffprobe binary | /opt/bin/ffprobe |

## Local Testing
```bash
# Install FFmpeg locally first
# macOS: brew install ffmpeg
# Ubuntu: apt install ffmpeg

python test_local.py
```

## Deployment

### Step 1: Create deployment package
```bash
# Create package directory
mkdir package
pip install -r requirements.txt -t package/
cp lambda_function.py package/
cd package
zip -r ../video-stitcher.zip .
cd ..
```

### Step 2: Deploy Lambda with FFmpeg Layer
```bash
# Get the FFmpeg layer ARN (from sampada's deployment)
# Or create your own layer from sampada/ffmpeg-layer/

aws lambda create-function \
  --function-name video-stitcher \
  --runtime python3.11 \
  --handler lambda_function.lambda_handler \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-role \
  --zip-file fileb://video-stitcher.zip \
  --timeout 900 \
  --memory-size 3008 \
  --ephemeral-storage Size=10240 \
  --layers arn:aws:lambda:us-east-1:YOUR_ACCOUNT:layer:ffmpeg:1

# Update existing function
aws lambda update-function-code \
  --function-name video-stitcher \
  --zip-file fileb://video-stitcher.zip
```

### Important Lambda Settings
- **Timeout**: 15 minutes (900 seconds) - video processing takes time
- **Memory**: 3008 MB minimum - FFmpeg needs memory
- **Ephemeral Storage**: 10 GB - for temp video files
- **FFmpeg Layer**: Required - provides ffmpeg and ffprobe binaries

## IAM Permissions Required
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::ai-demo-builder-bucket/videos/*",
        "arn:aws:s3:::ai-demo-builder-bucket/slides/*",
        "arn:aws:s3:::ai-demo-builder-bucket/output/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/Sessions"
    }
  ]
}
```

## Video Specifications
| Property | Value |
|----------|-------|
| Resolution | 1920x1080 (1080p) |
| Frame Rate | 30 fps |
| Video Codec | H.264 (libx264) |
| Audio Codec | AAC |
| Audio Sample Rate | 44100 Hz |
| Audio Channels | Stereo |
| Slide Duration | 3 seconds (configurable) |

## Error Handling
The service handles these scenarios:
- Videos without audio tracks (adds silent audio)
- Different video resolutions (normalizes to 1080p)
- Different frame rates (normalizes to 30fps)
- Missing or invalid files (skips and logs warning)