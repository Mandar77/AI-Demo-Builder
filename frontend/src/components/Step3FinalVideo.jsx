function Step4FinalVideo({ finalVideoUrl, processingStatus, statusData, onStartOver }) {
  // Extract progress information from statusData
  // Status Tracker returns: { status, progress: { percentage, message, uploaded, total }, ... }
  const progress = statusData?.progress || {}
  const progressPercentage = progress.percentage || 0
  const progressMessage = progress.message || 'Processing your videos...'
  const uploadedCount = progress.uploaded || statusData?.uploaded_videos_count || 0
  const totalVideos = progress.total || statusData?.suggestions_count || 0
  const currentStatus = statusData?.status || 'processing'

  return (
    <div className="max-w-3xl mx-auto text-center">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-3">
          Step 4: Your Demo Video
        </h2>
      </div>

      {processingStatus === 'processing' && (
        <div className="py-12">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-primary-600 mb-6"></div>
          
          {/* Status Message */}
          <p className="text-xl text-gray-700 mb-4 font-semibold">
            {progressMessage}
          </p>
          
          {/* Progress Bar */}
          <div className="max-w-md mx-auto mb-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">
                {currentStatus === 'uploading' && totalVideos > 0
                  ? `Uploaded ${uploadedCount} of ${totalVideos} videos`
                  : 'Processing...'}
              </span>
              <span className="text-sm font-medium text-primary-600">
                {Math.round(progressPercentage)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
              <div
                className="bg-primary-600 h-3 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${progressPercentage}%` }}
              ></div>
            </div>
          </div>

          {/* Additional Status Info */}
          {currentStatus && (
            <div className="mt-4">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-primary-100 text-primary-800">
                Status: {currentStatus.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </span>
            </div>
          )}

          <p className="text-gray-500 mt-4">
            This may take a few minutes. Please keep this page open.
          </p>
        </div>
      )}

      {processingStatus === 'failed' && (
        <div className="py-12">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 text-red-600 mb-4">
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <p className="text-xl text-gray-700 mb-2">Processing Failed</p>
          <p className="text-gray-500 mb-6">
            Something went wrong while processing your videos. Please try again.
          </p>
          <button
            onClick={onStartOver}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
          >
            Start Over
          </button>
        </div>
      )}

      {processingStatus === 'completed' && finalVideoUrl && (
        <div>
          <div className="bg-gray-900 rounded-xl overflow-hidden shadow-2xl mb-6">
            <video
              src={finalVideoUrl}
              controls
              className="w-full h-auto"
              autoPlay
            >
              Your browser does not support the video tag.
            </video>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-center mb-2">
              <div className="inline-flex items-center px-4 py-2 rounded-full bg-green-100 text-green-800">
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="font-semibold">Processing Complete!</span>
              </div>
            </div>
            <p className="text-lg text-gray-700">
              🎉 Your demo video is ready!
            </p>
            
            {/* Show project info if available */}
            {statusData?.project_name && (
              <p className="text-sm text-gray-500">
                Project: {statusData.project_name}
              </p>
            )}
            
            <div className="flex justify-center space-x-4">
              <a
                href={finalVideoUrl}
                download
                className="px-6 py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors inline-flex items-center"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download Video
              </a>
              
              <button
                onClick={onStartOver}
                className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
              >
                Create Another Demo
              </button>
            </div>
          </div>
        </div>
      )}

      {processingStatus === 'idle' && (
        <div className="py-12">
          <p className="text-gray-600">Waiting for video processing to complete...</p>
        </div>
      )}
    </div>
  )
}

export default Step4FinalVideo

