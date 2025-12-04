import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  response => response.data,
  error => {
    const errorMessage = error.response?.data?.error || error.message || 'An error occurred';
    console.error('API Error:', errorMessage);
    return Promise.reject(new Error(errorMessage));
  }
);

const api = {
  // Step 1: Analyze GitHub repository and create session
  async analyzeGitHub(githubUrl) {
    try {
      const response = await apiClient.post('/analyze', { github_url: githubUrl });
      
      // Check if this is the new format (with session_id) or old format (just analysis data)
      if (response.session_id) {
        // New format - already has session_id and suggestions
        return {
          sessionId: response.session_id,
          suggestions: response.suggestions?.videos || response.suggestions || [],
          analysisData: response, // Include full analysis data for display
        };
      } else {
        // Old format - only has analysis data
        const projectAnalysis = response.project_analysis || {};
        const suggestedSegments = projectAnalysis.suggestedSegments || 3;
        
        // Create mock suggestions based on analysis
        const suggestions = Array.from({ length: suggestedSegments }, (_, i) => ({
          id: `suggestion_${i + 1}`,
          title: `Video ${i + 1}`,
          description: `Record ${projectAnalysis.keyFeatures?.[i] || 'feature'} demonstration`,
          duration: 15,
        }));
        
        // Create session with the analysis data
        const sessionData = {
          github_url: githubUrl,
          project_name: projectAnalysis.projectName || 'Unknown Project',
          analysis: response,
        };
        
        const sessionResponse = await apiClient.post('/session', sessionData);
        
        return {
          sessionId: sessionResponse.session_id,
          suggestions,
          analysisData: response,
        };
      }
    } catch (error) {
      console.error('Error in analyzeGitHub:', error);
      throw error;
    }
  },

  // Step 2: Get AI suggestions (Aarzoo's service)
  async getSuggestions(analysisData) {
    const response = await apiClient.post('/suggestions', { 
      analysis: analysisData.project_analysis,
      readme: analysisData.parsed_readme
    });
    return response;
  },

  // Step 3: Create session (Aarzoo's service)
  async createSession(sessionData) {
    const response = await apiClient.post('/session', sessionData);
    return response;
  },

  // Step 4: Get upload URL (Sampada's service)
  async getUploadUrl(sessionId, suggestionId, fileName) {
    const response = await apiClient.post('/upload-url', {
      session_id: sessionId,
      suggestion_id: suggestionId,
      file_name: fileName
    });
    return response;
  },

  // Step 5: Check upload status (Sampada's service)
  async getUploadStatus(sessionId) {
    const response = await apiClient.get(`/upload-status?session_id=${sessionId}`);
    return response;
  },

  // Step 6: Get final demo video (Mandar's service)
  async getFinalVideo(sessionId) {
    const response = await apiClient.get(`/demo/${sessionId}`);
    return response;
  },

  // Step 7: Get session status (Chang's service)
  async getSessionStatus(sessionId) {
    const response = await apiClient.get(`/status/${sessionId}`);
    return response;
  }
};

export default api;