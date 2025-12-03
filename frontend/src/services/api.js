// Use the actual API Gateway URL from analysis pipeline
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://dez4stbz65.execute-api.us-west-1.amazonaws.com/prod'

export const api = {
  // Submit GitHub URL and get AI suggestions
  async analyzeGitHubRepo(githubUrl) {
    try {
      // First, call the analyze endpoint to get GitHub data
      const analyzeResponse = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ github_url: githubUrl }),
      })

      if (!analyzeResponse.ok) {
        const errorData = await analyzeResponse.json().catch(() => ({}))
        throw new Error(errorData.error || `Failed to analyze GitHub repository: ${analyzeResponse.status}`)
      }

      const analyzeData = await analyzeResponse.json()
      
      // Check if this is the new format (with session_id) or old format (just analysis data)
      if (analyzeData.session_id) {
        // Service 6 format - already has session_id and suggestions
        return {
          sessionId: analyzeData.session_id,
          suggestions: analyzeData.suggestions?.videos || analyzeData.suggestions || [],
        }
      } else {
        // Old format - only has analysis data, need to create session
        // For now, generate a temporary session ID and create mock suggestions
        // TODO: Call Service 6 to create session and get AI suggestions
        const sessionId = `temp-${Date.now()}`
        const projectAnalysis = analyzeData.project_analysis || {}
        const suggestedSegments = projectAnalysis.suggestedSegments || 3
        
        // Create mock suggestions based on analysis
        const suggestions = Array.from({ length: suggestedSegments }, (_, i) => ({
          id: i + 1,
          title: `Video ${i + 1}`,
          description: `Record ${projectAnalysis.keyFeatures?.[i] || 'feature'} demonstration`,
          duration: 15,
        }))
        
        return {
          sessionId,
          suggestions,
        }
      }
    } catch (error) {
      console.error('Error in analyzeGitHubRepo:', error)
      throw error
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

