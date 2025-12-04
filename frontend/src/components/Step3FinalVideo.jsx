import React from 'react';
import { Video, Download, Share2, CheckCircle, XCircle, Loader, RotateCcw } from 'lucide-react';
import LoadingSpinner from './LoadingSpinner';

function Step3FinalVideo({ finalVideoUrl, processingStatus, onStartOver }) {
  const handleDownload = () => {
    if (finalVideoUrl) {
      const link = document.createElement('a');
      link.href = finalVideoUrl;
      link.download = 'demo-video.mp4';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const handleShare = () => {
    if (navigator.share && finalVideoUrl) {
      navigator.share({
        title: 'Check out my demo video!',
        text: 'I created this demo video using AI Demo Builder',
        url: finalVideoUrl
      }).catch(console.error);
    } else {
      // Fallback: Copy to clipboard
      navigator.clipboard.writeText(finalVideoUrl).then(() => {
        alert('Video URL copied to clipboard!');
      });
    }
  };

  return (
    <div className="max-w-3xl mx-auto text-center">
      {processingStatus === 'processing' && (
        <div className="py-12">
          <div className="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full mb-6 animate-pulse">
            <Video className="w-12 h-12 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Creating Your Demo Video
          </h2>
          <p className="text-gray-600 mb-8">
            We're stitching your videos together and adding professional transitions...
          </p>
          <LoadingSpinner size="large" />
          <p className="text-sm text-gray-500 mt-4">This usually takes 1-2 minutes</p>
        </div>
      )}

      {processingStatus === 'complete' && finalVideoUrl && (
        <div className="py-8">
          <div className="inline-flex items-center justify-center w-24 h-24 bg-green-100 rounded-full mb-6">
            <CheckCircle className="w-16 h-16 text-green-600" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Your Demo Video is Ready!
          </h2>
          <p className="text-gray-600 mb-8">
            Your professional demo video has been created successfully.
          </p>

          {/* Video Player */}
          <div className="mb-8 rounded-lg overflow-hidden shadow-xl">
            <video
              controls
              className="w-full"
              src={finalVideoUrl}
            >
              Your browser does not support the video tag.
            </video>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
            <button
              onClick={handleDownload}
              className="btn-primary flex items-center justify-center"
            >
              <Download className="w-5 h-5 mr-2" />
              Download Video
            </button>
            <button
              onClick={handleShare}
              className="btn-secondary flex items-center justify-center"
            >
              <Share2 className="w-5 h-5 mr-2" />
              Share Video
            </button>
          </div>

          {/* Video URL */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-2">Direct Link:</p>
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={finalVideoUrl}
                readOnly
                className="flex-1 px-3 py-2 bg-white border border-gray-300 rounded text-sm"
                onClick={(e) => e.target.select()}
              />
              <button
                onClick={() => navigator.clipboard.writeText(finalVideoUrl)}
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded text-sm transition-colors"
              >
                Copy
              </button>
            </div>
          </div>
        </div>
      )}

      {processingStatus === 'failed' && (
        <div className="py-12">
          <div className="inline-flex items-center justify-center w-24 h-24 bg-red-100 rounded-full mb-6">
            <XCircle className="w-16 h-16 text-red-600" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Processing Failed
          </h2>
          <p className="text-gray-600 mb-8">
            Sorry, we encountered an error while creating your video. Please try again.
          </p>
        </div>
      )}

      {/* Start Over Button */}
      <button
        onClick={onStartOver}
        className="btn-secondary flex items-center justify-center mx-auto mt-8"
      >
        <RotateCcw className="w-5 h-5 mr-2" />
        Create Another Demo
      </button>
    </div>
  );
}

export default Step3FinalVideo;