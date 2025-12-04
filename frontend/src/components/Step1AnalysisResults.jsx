import React from 'react'
import { CheckCircle } from 'lucide-react'

function Step1AnalysisResults({ analysisData, githubUrl, onContinue, onBack }) {
  const { github_data, parsed_readme, project_analysis } = analysisData

  return (
    <div className="max-w-4xl mx-auto">
      {/* Success Message */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
          <CheckCircle className="w-10 h-10 text-green-600" />
        </div>
        <h2 className="text-3xl font-bold text-gray-900 mb-2">
          ✅ Analysis Complete!
        </h2>
        <p className="text-lg text-gray-600">
          Your repository has been analyzed. Review the results below, then continue to AI suggestions.
        </p>
      </div>

      {/* Analysis Results */}
      <div className="space-y-6">
        {/* Project Information */}
        <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
          <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
            <span className="mr-2">📦</span>
            Project Information
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Project Name</p>
              <p className="text-lg font-semibold text-gray-900">{github_data?.projectName || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Owner</p>
              <p className="text-lg font-semibold text-gray-900">{github_data?.owner || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Language</p>
              <p className="text-lg font-semibold text-gray-900">{github_data?.language || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Stars</p>
              <p className="text-lg font-semibold text-gray-900">
                {github_data?.stars?.toLocaleString() || 'N/A'}
              </p>
            </div>
          </div>
          {github_data?.topics && github_data.topics.length > 0 && (
            <div className="mt-4">
              <p className="text-sm text-gray-600 mb-2">Topics</p>
              <div className="flex flex-wrap gap-2">
                {github_data.topics.map((topic, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Project Analysis */}
        {project_analysis && (
          <div className="bg-purple-50 rounded-lg p-6 border border-purple-200">
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
              <span className="mr-2">🔍</span>
              Project Analysis
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Project Type</p>
                <p className="text-lg font-semibold text-gray-900 capitalize">
                  {project_analysis.projectType || 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Complexity</p>
                <p className="text-lg font-semibold text-gray-900 capitalize">
                  {project_analysis.complexity || 'N/A'}
                </p>
              </div>
            </div>
            {project_analysis.techStack && project_analysis.techStack.length > 0 && (
              <div className="mt-4">
                <p className="text-sm text-gray-600 mb-2">Tech Stack</p>
                <div className="flex flex-wrap gap-2">
                  {project_analysis.techStack.map((tech, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm"
                    >
                      {tech}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {project_analysis.keyFeatures && project_analysis.keyFeatures.length > 0 && (
              <div className="mt-4">
                <p className="text-sm text-gray-600 mb-2">Key Features</p>
                <ul className="list-disc list-inside space-y-1">
                  {project_analysis.keyFeatures.map((feature, index) => (
                    <li key={index} className="text-gray-900">
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* README Information */}
        {parsed_readme && (
          <div className="bg-green-50 rounded-lg p-6 border border-green-200">
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
              <span className="mr-2">📄</span>
              README Analysis
            </h3>
            {parsed_readme.title && (
              <div className="mb-4">
                <p className="text-sm text-gray-600">Title</p>
                <p className="text-lg font-semibold text-gray-900">{parsed_readme.title}</p>
              </div>
            )}
            {parsed_readme.features && parsed_readme.features.length > 0 && (
              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-2">Features</p>
                <ul className="list-disc list-inside space-y-1">
                  {parsed_readme.features.slice(0, 5).map((feature, index) => (
                    <li key={index} className="text-gray-900">
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <div className="mt-4">
              <p className="text-sm text-gray-600">Documentation Quality</p>
              <p className="text-lg font-semibold text-gray-900">
                {parsed_readme.hasDocumentation ? '✅ Good' : '⚠️ Limited'}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="mt-8 flex justify-between">
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
          Continue to AI Suggestions →
        </button>
      </div>
    </div>
  )
}

export default Step1AnalysisResults

