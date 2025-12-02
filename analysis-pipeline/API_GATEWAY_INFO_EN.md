# API Gateway Documentation

## 📌 Endpoint

```
POST https://dez4stbz65.execute-api.us-west-1.amazonaws.com/prod/analyze
Content-Type: application/json
```

## 📝 Request

```json
{
  "github_url": "https://github.com/owner/repo"
}
```

## 📤 Response

```json
{
  "github_data": {
    "projectName": "react",
    "owner": "facebook",
    "stars": 241023,
    "language": "JavaScript",
    "topics": ["declarative", "frontend", ...],
    "description": "...",
    "readme": "..."
  },
  "parsed_readme": {
    "title": "React",
    "features": ["Virtual DOM", "Component-based"],
    "installation": "npm install react",
    "usage": "import React from 'react'",
    "hasDocumentation": true
  },
  "project_analysis": {
    "projectType": "framework",
    "complexity": "high",
    "techStack": ["JavaScript", "React"],
    "keyFeatures": ["Virtual DOM", "Component-based"],
    "suggestedSegments": 8
  }
}
```

## 🧪 Examples

### JavaScript (fetch)

```javascript
fetch('https://dez4stbz65.execute-api.us-west-1.amazonaws.com/prod/analyze', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    github_url: 'https://github.com/facebook/react'
  })
})
.then(response => response.json())
.then(data => {
  console.log('Project:', data.github_data.projectName);
  console.log('Type:', data.project_analysis.projectType);
  console.log('Complexity:', data.project_analysis.complexity);
})
.catch(error => console.error('Error:', error));
```

### Python

```python
import requests

response = requests.post(
    'https://dez4stbz65.execute-api.us-west-1.amazonaws.com/prod/analyze',
    json={'github_url': 'https://github.com/facebook/react'}
)

result = response.json()
print(result['github_data']['projectName'])
print(result['project_analysis']['projectType'])
```

### curl

```bash
curl -X POST https://dez4stbz65.execute-api.us-west-1.amazonaws.com/prod/analyze \
  -H 'Content-Type: application/json' \
  -d '{"github_url": "https://github.com/facebook/react"}'
```

## ✅ CORS

CORS is enabled. You can call this API directly from web browsers.

## 🔒 Error Responses

| Status | Description |
|--------|-------------|
| 200 | Success |
| 400 | Bad Request (missing/invalid `github_url`) |
| 401 | Unauthorized (invalid GitHub token) |
| 403 | Forbidden (rate limit exceeded) |
| 404 | Repository not found |
| 500 | Internal server error |

Error format:
```json
{
  "error": "Error message"
}
```
