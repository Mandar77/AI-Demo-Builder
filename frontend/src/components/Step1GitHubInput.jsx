import React, { useState } from 'react';
import { Github, ArrowRight, AlertCircle, Loader } from 'lucide-react';
import api from '../services/api';
import { createPortal } from 'react-dom';

function Step1GitHubInput({ onSubmit, initialUrl }) {
  const [githubUrl, setGithubUrl] = useState(initialUrl || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [loadingMessage, setLoadingMessage] = useState('');

  const validateGitHubUrl = (url) => {
    const githubRegex = /^https?:\/\/(www\.)?github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\/?$/;
    return githubRegex.test(url);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!githubUrl.trim()) {
      setError('Please enter a GitHub URL');
      return;
    }

    if (!validateGitHubUrl(githubUrl)) {
      setError('Please enter a valid GitHub repository URL');
      return;
    }

    setLoading(true);
    try {
      // Step 1: Analyze repository
      setLoadingMessage('Analyzing repository...');
      const analysisResponse = await api.analyzeGitHub(githubUrl);
      console.log('📊 Analysis response:', analysisResponse);
      
      // Step 2: Get AI suggestions
      setLoadingMessage('Generating AI suggestions...');
      const suggestionsResponse = await api.getSuggestions(analysisResponse.analysis);
      console.log('💡 Suggestions response:', suggestionsResponse);
      
      // Extract suggestions from response (handle different structures)
      let suggestions = [];
      let sessionId = null;
      
      // Handle suggestionsResponse structure
      if (suggestionsResponse) {
        // Check for body wrapper (API Gateway format)
        let data = suggestionsResponse;
        if (suggestionsResponse.body) {
          data = typeof suggestionsResponse.body === 'string' 
            ? JSON.parse(suggestionsResponse.body) 
            : suggestionsResponse.body;
        }
        
        // Extract session_id
        sessionId = data.session_id || data.sessionId || suggestionsResponse.session_id;
        
        // Extract suggestions array
        if (data.suggestions) {
          suggestions = data.suggestions.videos || data.suggestions;
        } else if (data.videos) {
          suggestions = data.videos;
        } else if (data.video_suggestions) {
          suggestions = data.video_suggestions;
        } else if (Array.isArray(data)) {
          suggestions = data;
        }
      }
      
      console.log('📋 Extracted suggestions:', suggestions);
      console.log('🆔 Session ID:', sessionId);

      // If no session_id, create one from project name + timestamp
      if (!sessionId) {
        const projectName = analysisResponse.projectName || 'project';
        sessionId = `${projectName.toLowerCase().replace(/[^a-z0-9]/g, '_')}_${Date.now()}`;
        console.log('🆔 Generated session ID:', sessionId);
      }

      setLoadingMessage('Complete!');
      
      // Pass data to App.jsx in the expected format
      onSubmit({
        sessionId: sessionId,
        suggestions: Array.isArray(suggestions) ? suggestions : [],
        projectName: analysisResponse.projectName,
        analysisData: analysisResponse.analysis
      });
      
    } catch (err) {
      console.error('Error:', err);
      setError(err.message || 'Failed to analyze repository. Please try again.');
    } finally {
      setLoading(false);
      setLoadingMessage('');
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      {/* Full-screen loading overlay */}
      {loading && createPortal(
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]"
          style={{ margin: 0, padding: 0 }}
          onClick={(e) => e.stopPropagation()}
        >
          <div 
            className="bg-white rounded-lg p-8 max-w-md w-full mx-4 text-center"
            onClick={(e) => e.stopPropagation()}
          >
            <Loader className="w-12 h-12 animate-spin text-blue-600 mx-auto" />
            <h3 className="mt-4 text-xl font-semibold text-gray-900">
              {loadingMessage}
            </h3>
            <p className="mt-2 text-gray-600">
              This may take a few moments...
            </p>
            <div className="mt-4 space-y-2">
              <div className={`flex items-center text-sm justify-center ${loadingMessage.includes('Analyzing') ? 'text-blue-600' : 'text-green-600'}`}>
                <div className={`w-2 h-2 rounded-full mr-2 ${loadingMessage.includes('Analyzing') ? 'bg-blue-600 animate-pulse' : 'bg-green-600'}`}></div>
                Analyzing repository
              </div>
              <div className={`flex items-center text-sm justify-center ${loadingMessage.includes('Generating') ? 'text-blue-600' : loadingMessage.includes('Complete') ? 'text-green-600' : 'text-gray-400'}`}>
                <div className={`w-2 h-2 rounded-full mr-2 ${loadingMessage.includes('Generating') ? 'bg-blue-600 animate-pulse' : loadingMessage.includes('Complete') ? 'bg-green-600' : 'bg-gray-300'}`}></div>
                Generating AI suggestions
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}

      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full mb-4">
          <Github className="w-10 h-10 text-white" />
        </div>
        <h2 className="text-3xl font-bold text-gray-900 mb-3">
          Step 1: Enter Your GitHub Repository
        </h2>
        <p className="text-gray-600">
          Paste your GitHub repository URL and we'll analyze it to create demo suggestions
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="github-url" className="block text-sm font-medium text-gray-700 mb-2">
            GitHub Repository URL
          </label>
          <input
            id="github-url"
            type="url"
            value={githubUrl}
            onChange={(e) => setGithubUrl(e.target.value)}
            placeholder="https://github.com/username/repository"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            disabled={loading}
          />
          <p className="mt-2 text-sm text-gray-500">
            Example: https://github.com/facebook/react
          </p>
        </div>

        {error && (
          <div className="flex items-start space-x-2 text-red-600 bg-red-50 p-4 rounded-lg">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <p className="text-sm">{error}</p>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
        >
          {loading ? (
            <>
              <Loader className="w-5 h-5 animate-spin mr-2" />
              <span>Processing...</span>
            </>
          ) : (
            <>
              <span>Analyze Repository</span>
              <ArrowRight className="w-5 h-5 ml-2" />
            </>
          )}
        </button>
      </form>

      <div className="mt-8 p-6 bg-blue-50 rounded-lg">
        <h3 className="font-semibold text-gray-900 mb-2">What happens next?</h3>
        <ol className="space-y-2 text-sm text-gray-700">
          <li className="flex items-start">
            <span className="font-semibold mr-2">1.</span>
            We'll analyze your repository structure and README
          </li>
          <li className="flex items-start">
            <span className="font-semibold mr-2">2.</span>
            AI will generate personalized demo suggestions
          </li>
          <li className="flex items-start">
            <span className="font-semibold mr-2">3.</span>
            You'll record short video clips for each suggestion
          </li>
          <li className="flex items-start">
            <span className="font-semibold mr-2">4.</span>
            We'll automatically create a professional demo video
          </li>
        </ol>
      </div>
    </div>
  );
}

export default Step1GitHubInput;