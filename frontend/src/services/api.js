import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000,
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  response => response.data,
  error => {
    if (error.code === 'ECONNABORTED') {
      console.error('API Error: Request timeout');
      return Promise.reject(new Error('Request timeout - Lambda may be cold starting'));
    }
    if (error.code === 'ERR_NETWORK' || !error.response) {
      console.error('API Error: Network error - Cannot reach server');
      return Promise.reject(new Error('Network Error: Cannot reach the API server.'));
    }
    const errorMessage = error.response?.data?.error || error.message || 'An error occurred';
    console.error('API Error:', errorMessage);
    return Promise.reject(new Error(errorMessage));
  }
);

const api = {
  // =========================================
  // STEP 1: GitHub Analysis
  // =========================================
  async analyzeGitHub(githubUrl) {
    try {
      const response = await apiClient.post('/analyze', { github_url: githubUrl });
      
      console.log('📦 Raw /analyze response:', response);
      
      // Handle various response structures
      let data = response;
      
      // If response has a body property (API Gateway format)
      if (response.body) {
        data = typeof response.body === 'string' ? JSON.parse(response.body) : response.body;
        console.log('📦 Parsed body:', data);
      }
      
      // Return analysis data for getSuggestions to use
      return {
        analysis: data,
        projectName: data.github_data?.projectName || data.parsed_readme?.title || 'Demo Project'
      };
    } catch (error) {
      console.error('Error in analyzeGitHub:', error);
      throw error;
    }
  },

  async getSuggestions(analysisData) {
    console.log('📤 Sending to /ai-video-suggestion:', analysisData);
    const response = await apiClient.post('/ai-video-suggestion', { value: analysisData });
    console.log('📥 Raw suggestions response:', response);
    return response;
  },

  async createSession(sessionData) {
    const response = await apiClient.post('/session', sessionData);
    return response;
  },

  // =========================================
  // STEP 2: Video Upload
  // =========================================
  async getUploadUrl(sessionId, suggestionId, fileName) {
    const response = await apiClient.post('/upload-url', {
      session_id: sessionId,
      suggestion_id: suggestionId,
      file_name: fileName
    });
    if (typeof response.body === 'string') {
      return JSON.parse(response.body);
    }
    return response;
  },

  async getUploadStatus(sessionId) {
    const response = await apiClient.get(`/upload-status?session_id=${sessionId}`);
    return response;
  },

  // =========================================
  // STEP 3: Video Processing Pipeline
  // =========================================
  async startVideoProcessing(sessionId, uploadedVideos, projectName, suggestions = []) {
    console.log('🎬 Starting video processing pipeline for session:', sessionId);
    
    const mediaItems = [];
    
    // Add intro slide
    mediaItems.push({
      id: 'intro',
      type: 'slide',
      slideType: 'title',
      content: {
        title: projectName || 'Project Demo',
        subtitle: 'AI-Generated Demo Video',
        projectName: projectName || 'Demo'
      },
      order: 0,
      duration: 4
    });

    // Add uploaded videos with section slides
    const videoKeys = Object.keys(uploadedVideos).sort((a, b) => parseInt(a) - parseInt(b));
    videoKeys.forEach((key, index) => {
      const video = uploadedVideos[key];
      const suggestion = suggestions[index] || {};
      
      // Add section slide before each video
      mediaItems.push({
        id: `section_${index + 1}`,
        type: 'slide',
        slideType: 'section',
        content: {
          sectionNumber: index + 1,
          sectionTitle: suggestion.title || `Part ${index + 1}`,
          sectionDescription: suggestion.video_type || video.title || `Video segment ${index + 1}`
        },
        order: (index * 20) + 5,
        duration: 3
      });

      // IMPORTANT: Upload service saves to: videos/{session_id}/{suggestion_id}.mp4
      const s3Key = video.s3Key || `videos/${sessionId}/${key}.mp4`;
      
      mediaItems.push({
        type: 'video',
        key: s3Key,
        order: (index * 20) + 10
      });
    });

    // Add outro slide
    mediaItems.push({
      id: 'outro',
      type: 'slide',
      slideType: 'end',
      content: {
        title: 'Thank You!',
        subtitle: 'Generated with AI Demo Builder'
      },
      order: 9999,
      duration: 5
    });

    console.log('📋 Media items for processing:', mediaItems);

    const response = await apiClient.post('/process', {
      operation: 'start_pipeline',
      project_name: sessionId,
      payload: {
        media_items: mediaItems,
        options: {
          resolutions: ['720p'],
          generate_thumbnail: true,
          link_expiry: '7days'
        }
      }
    });

    return response;
  },

  async getProcessingStatus(sessionId) {
    try {
      const response = await apiClient.post('/process', {
        operation: 'status',
        project_name: sessionId
      });
      
      const data = response.data || response.body || response;
      
      // Parse body if it's a string
      let parsedData = data;
      if (typeof data === 'string') {
        try {
          parsedData = JSON.parse(data);
        } catch (e) {
          parsedData = {};
        }
      }

      // Parse outputs if it's a string
      let outputs = parsedData.outputs || [];
      if (typeof outputs === 'string') {
        try {
          outputs = JSON.parse(outputs);
        } catch (e) {
          outputs = [];
        }
      }

      return {
        status: parsedData.status || 'unknown',
        step: parsedData.processing_step || '',
        progress: parsedData.progress || 0,
        error: parsedData.error_message || null,
        demoUrl: parsedData.demo_url || null,
        thumbnailUrl: parsedData.thumbnail_url || null,
        outputs: outputs,
        updatedAt: parsedData.updated_at || null,
        exists: parsedData.exists !== false
      };
    } catch (error) {
      console.error('Error getting processing status:', error);
      throw error;
    }
  },

  async pollProcessingStatus(sessionId, onStatusUpdate, maxAttempts = 120, intervalMs = 5000) {
    return new Promise((resolve, reject) => {
      let attempts = 0;
      
      const poll = async () => {
        try {
          attempts++;
          const status = await this.getProcessingStatus(sessionId);
          
          console.log(`📊 Status poll #${attempts}:`, status.status, status.step);
          
          if (onStatusUpdate) {
            onStatusUpdate(status);
          }

          if (status.status === 'completed' || status.status === 'link_generated') {
            console.log('✅ Processing complete!');
            resolve(status);
            return;
          }

          if (status.status?.includes('failed') || status.status === 'error') {
            console.error('❌ Processing failed:', status.error);
            reject(new Error(status.error || 'Processing failed'));
            return;
          }

          if (attempts >= maxAttempts) {
            reject(new Error('Processing timeout - please check status manually'));
            return;
          }

          setTimeout(poll, intervalMs);
        } catch (error) {
          console.error('Polling error:', error);
          if (attempts >= maxAttempts) {
            reject(error);
          } else {
            setTimeout(poll, intervalMs);
          }
        }
      };

      poll();
    });
  },

  async getFinalVideo(sessionId) {
    const response = await apiClient.get(`/demo/${sessionId}`);
    return response;
  },

  async generatePublicLink(sessionId, options = {}) {
    const response = await apiClient.post('/process', {
      operation: 'generate_link',
      project_name: sessionId,
      resolution: options.resolution || '720p',
      expiry: options.expiry || '7days',
      include_thumbnail: options.includeThumbnail !== false
    });
    return response;
  },

  async getSessionStatus(sessionId) {
    const response = await apiClient.get(`/session/${sessionId}/status`);
    return response;
  },

  async healthCheck() {
    try {
      const response = await apiClient.get('/health');
      return { healthy: true, ...response };
    } catch (error) {
      return { healthy: false, error: error.message };
    }
  }
};

export default api;