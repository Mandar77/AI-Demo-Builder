function Step4FinalVideo({ finalVideoUrl, processingStatus, onStartOver }) {
  return (
    <div className="max-w-3xl mx-auto text-center">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-3">
          Step 4: Your Demo Video
        </h2>
      </div>

      {processingStatus === 'processing' && (
        <div className="py-12">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-primary-600 mb-4"></div>
          <p className="text-xl text-gray-700 mb-2">Processing your videos...</p>
          <p className="text-gray-500">
            We're stitching your clips together into a polished demo. This may take a few minutes.
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
            <p className="text-lg text-gray-700">
              🎉 Your demo video is ready!
            </p>
            
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

