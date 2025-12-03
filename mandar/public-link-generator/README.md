# Public Link Generator Service

Generates shareable public URLs for completed demo videos with configurable expiration.

## Features
- Generate presigned URLs with custom expiration
- Support for permanent links (via CloudFront)
- Multiple resolution support (1080p, 720p, 480p)
- Automatic thumbnail URL generation
- Track all generated links per session

## Operations

### Generate Single Link
```json
{
  "operation": "generate",
  "session_id": "abc123",
  "resolution": "720p",
  "expiry": "7days",
  "include_thumbnail": true
}
```

### Generate Links for All Resolutions
```json
{
  "operation": "generate_all",
  "session_id": "abc123",
  "expiry": "30days"
}
```

### Get All Links for Session
```json
{
  "operation": "get_links",
  "session_id": "abc123"
}
```

## Expiry Presets
| Preset | Duration |
|--------|----------|
| `1hour` | 1 hour |
| `24hours` | 24 hours |
| `7days` | 7 days (default) |
| `30days` | 30 days |
| `permanent` | No expiry (requires CloudFront) |

You can also pass a number (e.g., `"14"` for 14 days).

## Response Format
```json
{
  "success": true,
  "data": {
    "session_id": "abc123",
    "link_id": "xK9mP2nQ",
    "video_url": "https://...",
    "thumbnail_url": "https://...",
    "resolution": "720p",
    "file_size": 191804,
    "file_size_mb": "0.18",
    "url_type": "presigned",
    "created_at": "2024-12-03T00:50:00.000Z",
    "expires_at": "2024-12-10T00:50:00.000Z",
    "expires_in_seconds": 604800
  }
}
```

## Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| BUCKET_NAME | S3 bucket name | ai-demo-builder-bucket |
| TABLE_NAME | DynamoDB table | Sessions |
| BASE_URL | CloudFront URL (optional) | null |
| DEFAULT_EXPIRY_DAYS | Default expiry | 7 |
| MAX_EXPIRY_DAYS | Maximum allowed expiry | 30 |

## Local Testing
```bash
npm install
npm test
```

## Deployment
```bash
npm install
Compress-Archive -Path index.js, node_modules, package.json -DestinationPath public-link-generator.zip -Force
```

Or on PowerShell:
```powershell
Remove-Item public-link-generator.zip -ErrorAction SilentlyContinue
Compress-Archive -Path index.js, node_modules, package.json -DestinationPath public-link-generator.zip -Force
```

Lambda Configuration:
- Runtime: Node.js 18.x
- Handler: index.handler
- Timeout: 30 seconds
- Memory: 256 MB

## IAM Permissions Required
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:HeadObject"
      ],
      "Resource": "arn:aws:s3:::ai-demo-builder-bucket/final/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/Sessions"
    }
  ]
}
```

## Integration with Frontend

The frontend can use the generated URL directly:

```javascript
// Get shareable link
const response = await fetch('/api/public-link', {
  method: 'POST',
  body: JSON.stringify({
    session_id: sessionId,
    resolution: '720p',
    expiry: '7days'
  })
});

const { data } = await response.json();

// Use the URL
window.open(data.video_url, '_blank');

// Or copy to clipboard
navigator.clipboard.writeText(data.video_url);
```