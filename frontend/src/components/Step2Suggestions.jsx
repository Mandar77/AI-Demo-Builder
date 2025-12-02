function Step2Suggestions({ suggestions, onContinue, onBack }) {
  if (!suggestions || suggestions.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600 mb-4">No suggestions available.</p>
        <button
          onClick={onBack}
          className="text-primary-600 hover:text-primary-700 font-medium"
        >
          Go back
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-3">
          Step 2: AI Suggestions
        </h2>
        <p className="text-gray-600">
          Based on your repository, here's what we recommend you record:
        </p>
      </div>

      <div className="space-y-4 mb-8">
        {suggestions.map((suggestion, index) => (
          <div
            key={suggestion.id || index}
            className="p-6 bg-gradient-to-r from-primary-50 to-blue-50 rounded-xl border border-primary-200 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-start">
              <div className="flex-shrink-0 w-8 h-8 bg-primary-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                {index + 1}
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {suggestion.title || `Video ${index + 1}`}
                </h3>
                <p className="text-gray-700 leading-relaxed">
                  {suggestion.description || suggestion.text || suggestion}
                </p>
                {suggestion.duration && (
                  <p className="mt-2 text-sm text-gray-500">
                    Suggested duration: {suggestion.duration}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="flex justify-between">
        <button
          onClick={onBack}
          className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
        >
          Back
        </button>
        <button
          onClick={onContinue}
          className="px-6 py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
        >
          Continue to Upload
        </button>
      </div>
    </div>
  )
}

export default Step2Suggestions

