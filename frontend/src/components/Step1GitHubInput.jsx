import { useState } from 'react'
import { api } from '../services/api'

function Step1GitHubInput({ onSubmit, initialUrl }) {
  const [githubUrl, setGithubUrl] = useState(initialUrl || '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    
    // Validate GitHub URL
    const githubRegex = /^https?:\/\/(www\.)?github\.com\/[\w\-\.]+\/[\w\-\.]+/
    if (!githubRegex.test(githubUrl)) {
      setError('Please enter a valid GitHub repository URL')
      return
    }

    setLoading(true)
    try {
      const { sessionId, suggestions } = await api.analyzeGitHubRepo(githubUrl)
      onSubmit(githubUrl, sessionId, suggestions)
    } catch (err) {
      setError(err.message || 'Failed to analyze repository. Please try again.')
      console.error('Error analyzing GitHub repo:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-3">
          Step 1: Share Your GitHub Repository
        </h2>
        <p className="text-gray-600">
          Paste the link to your GitHub repository and our AI will analyze it to suggest what videos to record.
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
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-lg"
            disabled={loading}
            required
          />
          {error && (
            <p className="mt-2 text-sm text-red-600">{error}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={loading || !githubUrl}
          className="w-full bg-primary-600 text-white py-3 px-6 rounded-lg font-semibold text-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Analyzing repository...
            </span>
          ) : (
            'Analyze Repository'
          )}
        </button>
      </form>

      <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <p className="text-sm text-blue-800">
          <strong>Example:</strong> If you have a search app, our AI might suggest:
          "Record the search bar, show typing a query, show the results."
        </p>
      </div>
    </div>
  )
}

export default Step1GitHubInput

