const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/prod'

export const api = {
  // Submit GitHub URL and get AI suggestions
  async analyzeGitHubRepo(githubUrl) {
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ github_url: githubUrl }),
    })

    if (!response.ok) {
      throw new Error('Failed to analyze GitHub repository')
    }

    const data = await response.json()
    return {
      sessionId: data.session_id,
      suggestions: data.suggestions || [],
    }
  },

  // Get upload URL for a specific video
  async getUploadUrl(sessionId, suggestionId) {
    const response = await fetch(`${API_BASE_URL}/upload-url`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        suggestion_id: suggestionId,
      }),
    })

    if (!response.ok) {
      throw new Error('Failed to get upload URL')
    }

    const data = await response.json()
    return data.upload_url
  },

  // Upload video to S3 using presigned URL
  async uploadVideo(uploadUrl, file) {
    const response = await fetch(uploadUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': 'video/mp4',
      },
      body: file,
    })

    if (!response.ok) {
      throw new Error('Failed to upload video')
    }

    return true
  },

  // Get session status
  async getSessionStatus(sessionId) {
    const response = await fetch(`${API_BASE_URL}/session/${sessionId}/status`)

    if (!response.ok) {
      throw new Error('Failed to get session status')
    }

    return await response.json()
  },
}

