import React, { useState, useCallback } from 'react';
import Step1GitHubInput from './components/Step1GitHubInput';
import Step2SuggestionsWithUpload from './components/Step2SuggestionsWithUpload';
import Step3FinalVideo from './components/Step3FinalVideo';
import { Github, Sparkles, Video } from 'lucide-react';
import api from './services/api';

function App() {
  const [currentStep, setCurrentStep] = useState(1);
  const [sessionId, setSessionId] = useState(null);
  const [projectName, setProjectName] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [uploadedVideos, setUploadedVideos] = useState({});
  
  const [processingStatus, setProcessingStatus] = useState({
    status: 'idle',
    step: '',
    progress: 0,
    error: null
  });
  const [finalVideoUrl, setFinalVideoUrl] = useState(null);
  const [thumbnailUrl, setThumbnailUrl] = useState(null);

  const handleStep1Complete = useCallback((data) => {
    console.log('Step 1 complete:', data);
    setSessionId(data.sessionId);
    setSuggestions(data.suggestions || []);
    setProjectName(data.projectName || data.analysisData?.repo_name || 'Demo Project');
    setCurrentStep(2);
  }, []);

  const handleAllVideosUploaded = useCallback(async (videos) => {
    console.log('All videos uploaded:', videos);
    setUploadedVideos(videos);
    setCurrentStep(3);
    
    setProcessingStatus({
      status: 'starting',
      step: 'Initializing video processing pipeline...',
      progress: 5,
      error: null
    });

    try {
      // Transform uploaded videos with CORRECT S3 keys
      // Upload service saves to: videos/{session_id}/{suggestion_id}.mp4
      const videosWithKeys = {};
      Object.entries(videos).forEach(([key, fileName]) => {
        videosWithKeys[key] = {
          fileName: typeof fileName === 'string' ? fileName : fileName.fileName,
          s3Key: `videos/${sessionId}/${key}.mp4`,  // CORRECT PATH
          title: suggestions[parseInt(key) - 1]?.title || `Video ${key}`
        };
      });

      console.log('🚀 Starting video processing with keys:', videosWithKeys);
      await api.startVideoProcessing(sessionId, videosWithKeys, projectName, suggestions);

      const finalStatus = await api.pollProcessingStatus(
        sessionId,
        (status) => {
          setProcessingStatus({
            status: status.status,
            step: getStatusMessage(status.status, status.step),
            progress: calculateProgress(status.status),
            error: status.error
          });

          if (status.demoUrl) {
            setFinalVideoUrl(status.demoUrl);
          }
          if (status.thumbnailUrl) {
            setThumbnailUrl(status.thumbnailUrl);
          }
        },
        120,
        5000
      );

      console.log('✅ Processing complete:', finalStatus);
      setFinalVideoUrl(finalStatus.demoUrl);
      setThumbnailUrl(finalStatus.thumbnailUrl);
      setProcessingStatus({
        status: 'completed',
        step: 'Your demo video is ready!',
        progress: 100,
        error: null
      });

    } catch (error) {
      console.error('❌ Processing error:', error);
      setProcessingStatus({
        status: 'failed',
        step: 'Processing failed',
        progress: 0,
        error: error.message
      });
    }
  }, [sessionId, projectName, suggestions]);

  const handleBack = useCallback(() => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  }, [currentStep]);

  const handleStartOver = useCallback(() => {
    setCurrentStep(1);
    setSessionId(null);
    setProjectName('');
    setSuggestions([]);
    setUploadedVideos({});
    setProcessingStatus({ status: 'idle', step: '', progress: 0, error: null });
    setFinalVideoUrl(null);
    setThumbnailUrl(null);
  }, []);

  const getStatusMessage = (status, step) => {
    const messages = {
      'starting': 'Initializing pipeline...',
      'queued': 'Job queued for processing...',
      'processing': step || 'Processing videos...',
      'generating_slides': 'Creating transition slides...',
      'slides_ready': 'Slides created! Starting video stitching...',
      'stitching': step || 'Stitching videos together...',
      'stitched': 'Videos stitched! Optimizing...',
      'optimizing': step || 'Optimizing video quality...',
      'generating_link': 'Generating shareable link...',
      'completed': 'Your demo video is ready!',
      'link_generated': 'Your demo video is ready!',
      'failed': 'Processing failed',
      'stitching_failed': 'Video stitching failed',
      'optimization_failed': 'Video optimization failed'
    };
    return messages[status] || step || status || 'Processing...';
  };

  const calculateProgress = (status) => {
    const progressMap = {
      'starting': 5,
      'queued': 10,
      'processing': 15,
      'generating_slides': 25,
      'slides_ready': 35,
      'stitching': 50,
      'stitched': 70,
      'optimizing': 85,
      'generating_link': 95,
      'completed': 100,
      'link_generated': 100
    };
    return progressMap[status] || 0;
  };

  const StepIndicator = () => (
    <div className="flex items-center justify-center space-x-4 mb-8">
      {[
        { num: 1, icon: Github, label: 'GitHub URL' },
        { num: 2, icon: Sparkles, label: 'Record Videos' },
        { num: 3, icon: Video, label: 'Final Demo' }
      ].map((step, index) => (
        <React.Fragment key={step.num}>
          <div className="flex flex-col items-center">
            <div
              className={`w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 ${
                currentStep >= step.num
                  ? 'bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-lg'
                  : 'bg-gray-200 text-gray-500'
              }`}
            >
              {currentStep > step.num ? (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <step.icon className="w-6 h-6" />
              )}
            </div>
            <span className={`mt-2 text-sm font-medium ${
              currentStep >= step.num ? 'text-gray-900' : 'text-gray-500'
            }`}>
              {step.label}
            </span>
          </div>
          {index < 2 && (
            <div className={`w-16 h-1 rounded ${
              currentStep > step.num ? 'bg-gradient-to-r from-blue-500 to-purple-600' : 'bg-gray-200'
            }`} />
          )}
        </React.Fragment>
      ))}
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <header className="py-6 px-4">
        <div className="max-w-6xl mx-auto text-center">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
            AI Demo Builder
          </h1>
          <p className="text-gray-600">
            Transform your GitHub project into a professional demo video with AI-powered suggestions
          </p>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4">
        <StepIndicator />
      </div>

      <main className="max-w-6xl mx-auto px-4 pb-12">
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          {currentStep === 1 && (
            <Step1GitHubInput
              onSubmit={handleStep1Complete}
              initialUrl=""
            />
          )}

          {currentStep === 2 && (
            <Step2SuggestionsWithUpload
              sessionId={sessionId}
              suggestions={suggestions}
              onAllVideosUploaded={handleAllVideosUploaded}
              onBack={handleBack}
            />
          )}

          {currentStep === 3 && (
            <Step3FinalVideo
              sessionId={sessionId}
              projectName={projectName}
              finalVideoUrl={finalVideoUrl}
              thumbnailUrl={thumbnailUrl}
              processingStatus={processingStatus}
              onStartOver={handleStartOver}
            />
          )}
        </div>
      </main>

      <footer className="py-4 text-center text-gray-500 text-sm">
        AI Demo Builder • Cloud Computing Final Project • Fall 2025
      </footer>
    </div>
  );
}

export default App;