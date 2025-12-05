import React, { useState } from 'react';
import Step1GitHubInput from './components/Step1GitHubInput';
import Step2SuggestionsWithUpload from './components/Step2SuggestionsWithUpload';
import Step3FinalVideo from './components/Step3FinalVideo';
import { Github, Sparkles, Video } from 'lucide-react';

function App() {
  const [step, setStep] = useState(1);
  const [sessionId, setSessionId] = useState(null);
  const [githubUrl, setGithubUrl] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [uploadedVideos, setUploadedVideos] = useState({});
  const [finalVideoUrl, setFinalVideoUrl] = useState(null);
  const [processingStatus, setProcessingStatus] = useState('idle');

  const handleGitHubSubmit = (url, suggestionsData) => {
    setGithubUrl(url);
    setSessionId(suggestionsData["session_id"]);
    setSuggestions(suggestionsData["videos"]);
    setStep(2);
  };

  const handleAllVideosUploaded = (videos) => {
    setUploadedVideos(videos);
    setStep(3);
    setProcessingStatus('processing');
    pollForFinalVideo();
  };

  const pollForFinalVideo = () => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_URL}/demo/${sessionId}`
        );
        
        if (response.ok) {
          const data = await response.json();
          if (data.status === 'complete' && data.demo_url) {
            setFinalVideoUrl(data.demo_url);
            setProcessingStatus('complete');
            clearInterval(interval);
          } else if (data.status === 'failed') {
            setProcessingStatus('failed');
            clearInterval(interval);
          }
        }
      } catch (error) {
        console.error('Error polling for final video:', error);
      }
    }, 3000);

    // Stop polling after 5 minutes
    setTimeout(() => clearInterval(interval), 300000);
  };

  const handleStartOver = () => {
    setStep(1);
    setSessionId(null);
    setGithubUrl('');
    setSuggestions([]);
    setUploadedVideos({});
    setFinalVideoUrl(null);
    setProcessingStatus('idle');
  };

  const steps = [
    { num: 1, label: 'GitHub URL', icon: Github },
    { num: 2, label: 'Record Videos', icon: Sparkles },
    { num: 3, label: 'Final Demo', icon: Video }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <header className="text-center mb-12">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
            AI Demo Builder
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Transform your GitHub project into a professional demo video with AI-powered suggestions
          </p>
        </header>

        {/* Progress Steps */}
        <div className="mb-12">
          <div className="flex items-center justify-center space-x-4 md:space-x-8">
            {steps.map((stepItem, index) => {
              const Icon = stepItem.icon;
              return (
                <React.Fragment key={stepItem.num}>
                  <div className="flex flex-col items-center">
                    <div
                      className={`w-16 h-16 rounded-full flex items-center justify-center transition-all duration-300 ${
                        step >= stepItem.num
                          ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg transform scale-110'
                          : 'bg-gray-200 text-gray-500'
                      }`}
                    >
                      {step > stepItem.num ? (
                        <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <Icon className="w-8 h-8" />
                      )}
                    </div>
                    <span className={`mt-2 text-sm font-medium ${
                      step >= stepItem.num ? 'text-gray-900' : 'text-gray-500'
                    }`}>
                      {stepItem.label}
                    </span>
                  </div>
                  {index < steps.length - 1 && (
                    <div
                      className={`hidden md:block w-24 h-1 transition-all duration-300 ${
                        step > stepItem.num 
                          ? 'bg-gradient-to-r from-blue-500 to-purple-600' 
                          : 'bg-gray-200'
                      }`}
                    />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>

        {/* Step Content */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          {step === 1 && (
            <div className="p-8">
              <Step1GitHubInput
                onSubmit={handleGitHubSubmit}
                initialUrl={githubUrl}
              />
            </div>
          )}
          
          {step === 2 && (
            <Step2SuggestionsWithUpload
              sessionId={sessionId}
              suggestions={suggestions}
              onAllVideosUploaded={handleAllVideosUploaded}
              onBack={() => setStep(1)}
            />
          )}
          
          {step === 3 && (
            <div className="p-8">
              <Step3FinalVideo
                finalVideoUrl={finalVideoUrl}
                processingStatus={processingStatus}
                onStartOver={handleStartOver}
              />
            </div>
          )}
        </div>

        {/* Footer */}
        <footer className="mt-12 text-center text-gray-500 text-sm">
          <p>AI Demo Builder • Cloud Computing Final Project • Fall 2025</p>
        </footer>
      </div>
    </div>
  );
}

export default App;