import React from 'react'
import { Video, CheckCircle } from 'lucide-react'

function Step2Suggestions({ suggestions, onContinue, onBack }) {
  return (
    <div className="max-w-4xl mx-auto p-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-3">
          AI-Generated Demo Suggestions
        </h2>
        <p className="text-gray-600 mb-4">
          Review the AI-generated suggestions for your demo video. These are based on your project analysis.
        </p>
      </div>

      {/* Suggestions List */}
      <div className="space-y-4 mb-8">
        {suggestions.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p>No suggestions available. Please try again.</p>
          </div>
        ) : (
          suggestions.map((suggestion, index) => (
            <div
              key={suggestion.id || index}
              className="rounded-xl border-2 border-gray-200 bg-white hover:shadow-md transition-all duration-300"
            >
              <div className="p-6">
                {/* Suggestion Header */}
                <div className="flex items-start">
                  <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {suggestion.title || `Video Segment ${index + 1}`}
                    </h3>
                    <p className="text-gray-700 mb-2">
                      {suggestion.description || suggestion.text || suggestion}
                    </p>
                    {suggestion.duration && (
                      <p className="text-sm text-gray-500">
                        <span className="inline-flex items-center">
                          <Video className="w-4 h-4 mr-1" />
                          Suggested duration: {suggestion.duration} seconds
                        </span>
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex justify-between mt-8">
        <button
          onClick={onBack}
          className="px-6 py-3 border border-gray-300 rounded-lg font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
        >
          Back
        </button>
        <button
          onClick={onContinue}
          className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg font-semibold hover:from-blue-600 hover:to-purple-700 transition-colors"
        >
          Continue to Upload Videos →
        </button>
      </div>
    </div>
  )
}

export default Step2Suggestions

