import React from 'react';
import { Video, Download, Share2, CheckCircle, XCircle, RotateCcw, Loader, Image, FileVideo, Wand2, Link } from 'lucide-react';

const STATUS_INFO = {
  idle: { label: 'Waiting', color: 'gray', icon: null },
  starting: { label: 'Starting', color: 'blue', icon: Loader },
  queued: { label: 'Queued', color: 'yellow', icon: Loader },
  processing: { label: 'Processing', color: 'blue', icon: Loader },
  generating_slides: { label: 'Generating Slides', color: 'blue', icon: Image },
  slides_ready: { label: 'Slides Ready', color: 'green', icon: CheckCircle },
  stitching: { label: 'Stitching Videos', color: 'blue', icon: FileVideo },
  stitched: { label: 'Video Stitched', color: 'green', icon: CheckCircle },
  optimizing: { label: 'Optimizing Video', color: 'blue', icon: Wand2 },
  generating_link: { label: 'Generating Link', color: 'blue', icon: Link },
  completed: { label: 'Complete!', color: 'green', icon: CheckCircle },
  link_generated: { label: 'Ready to Share!', color: 'green', icon: Link },
  failed: { label: 'Failed', color: 'red', icon: XCircle },
  stitching_failed: { label: 'Stitching Failed', color: 'red', icon: XCircle },
  optimization_failed: { label: 'Optimization Failed', color: 'red', icon: XCircle },
  slides_failed: { label: 'Slide Generation Failed', color: 'red', icon: XCircle },
};

const PIPELINE_STEPS = [
  { key: 'generating_slides', label: 'Generate Slides', icon: Image },
  { key: 'stitching', label: 'Stitch Videos', icon: FileVideo },
  { key: 'optimizing', label: 'Optimize', icon: Wand2 },
  { key: 'completed', label: 'Complete', icon: CheckCircle },
];

function getStepStatus(currentStatus, stepKey) {
  const statusOrder = ['starting', 'generating_slides', 'slides_ready', 'stitching', 'stitched', 'optimizing', 'generating_link', 'completed', 'link_generated'];
  const currentIndex = statusOrder.indexOf(currentStatus);
  
  if (stepKey === 'generating_slides' && currentIndex >= statusOrder.indexOf('slides_ready')) return 'complete';
  if (stepKey === 'stitching' && currentIndex >= statusOrder.indexOf('stitched')) return 'complete';
  if (stepKey === 'optimizing' && currentIndex >= statusOrder.indexOf('completed')) return 'complete';
  if (stepKey === 'completed' && (currentStatus === 'completed' || currentStatus === 'link_generated')) return 'complete';
  
  if (currentStatus === stepKey) return 'active';
  if (currentStatus === 'slides_ready' && stepKey === 'generating_slides') return 'complete';
  if (currentStatus === 'stitched' && stepKey === 'stitching') return 'complete';
  
  return 'pending';
}

// processingStatus is now an OBJECT with { status, step, progress, error }
function Step3FinalVideo({ finalVideoUrl, thumbnailUrl, processingStatus, onStartOver }) {
  // Destructure the processingStatus object
  const status = processingStatus?.status || 'idle';
  const step = processingStatus?.step || '';
  const progress = processingStatus?.progress || 0;
  const error = processingStatus?.error || null;

  const statusInfo = STATUS_INFO[status] || STATUS_INFO.processing;
  const isProcessing = !['completed', 'link_generated', 'failed', 'stitching_failed', 'optimization_failed', 'slides_failed'].includes(status);
  const isFailed = status.includes('failed');
  const isComplete = status === 'completed' || status === 'link_generated';

  const handleDownload = () => {
    if (finalVideoUrl) {
      const link = document.createElement('a');
      link.href = finalVideoUrl;
      link.download = 'demo-video.mp4';
      link.target = '_blank';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const handleShare = async () => {
    if (navigator.share && finalVideoUrl) {
      try {
        await navigator.share({
          title: 'Check out my demo video!',
          text: 'I created this demo video using AI Demo Builder',
          url: finalVideoUrl
        });
      } catch (err) {
        if (err.name !== 'AbortError') {
          copyToClipboard();
        }
      }
    } else {
      copyToClipboard();
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(finalVideoUrl).then(() => {
      alert('Video URL copied to clipboard!');
    });
  };

  return (
    <div className="max-w-3xl mx-auto p-6">
      {/* Processing State */}
      {isProcessing && (
        <div className="py-8 text-center">
          <div className="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full mb-6 animate-pulse">
            <Video className="w-12 h-12 text-white" />
          </div>
          
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Creating Your Demo Video
          </h2>
          
          <p className="text-gray-600 mb-2">
            {step || 'Processing your video...'}
          </p>
          
          {/* Current Status Badge */}
          <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium mb-8 ${
            statusInfo.color === 'blue' ? 'bg-blue-100 text-blue-800' :
            statusInfo.color === 'green' ? 'bg-green-100 text-green-800' :
            statusInfo.color === 'yellow' ? 'bg-yellow-100 text-yellow-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {statusInfo.icon && <statusInfo.icon className="w-4 h-4 mr-2 animate-spin" />}
            {statusInfo.label}
          </div>

          {/* Progress Bar */}
          <div className="max-w-md mx-auto mb-6">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>Progress</span>
              <span>{progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-gradient-to-r from-blue-500 to-purple-600 h-3 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Pipeline Progress */}
          <div className="max-w-lg mx-auto mb-8">
            <div className="flex items-center justify-between">
              {PIPELINE_STEPS.map((pipelineStep, index) => {
                const stepStatus = getStepStatus(status, pipelineStep.key);
                const Icon = pipelineStep.icon;
                
                return (
                  <React.Fragment key={pipelineStep.key}>
                    <div className="flex flex-col items-center">
                      <div className={`w-12 h-12 rounded-full flex items-center justify-center transition-all duration-500 ${
                        stepStatus === 'complete' ? 'bg-green-500 text-white' :
                        stepStatus === 'active' ? 'bg-blue-500 text-white animate-pulse' :
                        'bg-gray-200 text-gray-400'
                      }`}>
                        {stepStatus === 'complete' ? (
                          <CheckCircle className="w-6 h-6" />
                        ) : stepStatus === 'active' ? (
                          <Loader className="w-6 h-6 animate-spin" />
                        ) : (
                          <Icon className="w-6 h-6" />
                        )}
                      </div>
                      <span className={`mt-2 text-xs font-medium ${
                        stepStatus === 'complete' ? 'text-green-600' :
                        stepStatus === 'active' ? 'text-blue-600' :
                        'text-gray-400'
                      }`}>
                        {pipelineStep.label}
                      </span>
                    </div>
                    
                    {index < PIPELINE_STEPS.length - 1 && (
                      <div className={`flex-1 h-1 mx-2 rounded transition-all duration-500 ${
                        getStepStatus(status, PIPELINE_STEPS[index + 1].key) !== 'pending' 
                          ? 'bg-green-500' 
                          : 'bg-gray-200'
                      }`} />
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          </div>

          <p className="text-sm text-gray-500 mt-4">This usually takes 1-3 minutes</p>
        </div>
      )}

      {/* Success State */}
      {isComplete && finalVideoUrl && (
        <div className="py-8">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-24 h-24 bg-green-100 rounded-full mb-6">
              <CheckCircle className="w-16 h-16 text-green-600" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Your Demo Video is Ready! 🎉
            </h2>
            <p className="text-gray-600">
              Your professional demo video has been created successfully.
            </p>
          </div>

          {thumbnailUrl && (
            <div className="mb-4 flex justify-center">
              <img 
                src={thumbnailUrl} 
                alt="Video thumbnail" 
                className="rounded-lg shadow-md max-w-xs"
              />
            </div>
          )}

          <div className="mb-8 rounded-lg overflow-hidden shadow-xl bg-black">
            <video
              controls
              className="w-full"
              src={finalVideoUrl}
              poster={thumbnailUrl}
            >
              Your browser does not support the video tag.
            </video>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
            <button
              onClick={handleDownload}
              className="inline-flex items-center justify-center px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all shadow-md hover:shadow-lg"
            >
              <Download className="w-5 h-5 mr-2" />
              Download Video
            </button>
            <button
              onClick={handleShare}
              className="inline-flex items-center justify-center px-6 py-3 bg-white border-2 border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition-all"
            >
              <Share2 className="w-5 h-5 mr-2" />
              Share Video
            </button>
          </div>

          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-2">Direct Link (valid for 7 days):</p>
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={finalVideoUrl}
                readOnly
                className="flex-1 px-3 py-2 bg-white border border-gray-300 rounded text-sm font-mono truncate"
                onClick={(e) => e.target.select()}
              />
              <button
                onClick={copyToClipboard}
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded text-sm transition-colors whitespace-nowrap"
              >
                Copy
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Failed State */}
      {isFailed && (
        <div className="py-12 text-center">
          <div className="inline-flex items-center justify-center w-24 h-24 bg-red-100 rounded-full mb-6">
            <XCircle className="w-16 h-16 text-red-600" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Processing Failed
          </h2>
          <p className="text-gray-600 mb-4">
            {error || 'Sorry, we encountered an error while creating your video.'}
          </p>
          <p className="text-sm text-gray-500 mb-8">
            Status: {statusInfo.label}
          </p>
        </div>
      )}

      {/* Start Over Button */}
      <div className="text-center mt-8">
        <button
          onClick={onStartOver}
          className="inline-flex items-center justify-center px-6 py-3 bg-white border-2 border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition-all"
        >
          <RotateCcw className="w-5 h-5 mr-2" />
          Create Another Demo
        </button>
      </div>
    </div>
  );
}

export default Step3FinalVideo;