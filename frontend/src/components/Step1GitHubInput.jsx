import React, { useState } from 'react';
import { Github, ArrowRight, AlertCircle } from 'lucide-react';
import api from '../services/api';
import LoadingSpinner from './LoadingSpinner';

function Step1GitHubInput({ onSubmit, initialUrl }) {
  const [githubUrl, setGithubUrl] = useState(initialUrl || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [loadingMessage, setLoadingMessage] = useState('');

  const validateGitHubUrl = (url) => {
    const githubRegex = /^https?:\/\/(www\.)?github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\/?$/;
    return githubRegex.test(url);
  };

  // When the user clicks on the 'Analyze Repo' button
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
      
      // Step 2: Get AI suggestions
      setLoadingMessage('Generating AI suggestions...');
      const suggestionsResponse = await api.getSuggestions(analysisResponse['analysis']);

      setLoadingMessage('Complete!');
      
      onSubmit(
        githubUrl,
        suggestionsResponse
      );
    } catch (err) {
      console.error('Error:', err);
      setError(err.message || 'Failed to analyze repository. Please try again.');
    } finally {
      setLoading(false);
      setLoadingMessage('');
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Full-screen loading overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 text-center">
            <LoadingSpinner />
            <h3 className="mt-4 text-xl font-semibold text-gray-900">
              {loadingMessage}
            </h3>
            <p className="mt-2 text-gray-600">
              This may take a few moments...
            </p>
            <div className="mt-4 space-y-2">
              <div className={`flex items-center text-sm ${loadingMessage.includes('Analyzing') ? 'text-blue-600' : 'text-green-600'}`}>
                <div className={`w-2 h-2 rounded-full mr-2 ${loadingMessage.includes('Analyzing') ? 'bg-blue-600 animate-pulse' : 'bg-green-600'}`}></div>
                Analyzing repository
              </div>
              <div className={`flex items-center text-sm ${loadingMessage.includes('Generating') ? 'text-blue-600' : loadingMessage.includes('Complete') ? 'text-green-600' : 'text-gray-400'}`}>
                <div className={`w-2 h-2 rounded-full mr-2 ${loadingMessage.includes('Generating') ? 'bg-blue-600 animate-pulse' : loadingMessage.includes('Complete') ? 'bg-green-600' : 'bg-gray-300'}`}></div>
                Generating AI suggestions
              </div>
            </div>
          </div>
        </div>
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
            className="input-field"
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
          className="w-full btn-primary flex items-center justify-center"
        >
          {loading ? (
            <>
              <LoadingSpinner />
              <span className="ml-2">Processing...</span>
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