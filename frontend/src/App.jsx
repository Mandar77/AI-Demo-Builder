import { useState } from 'react'
import Step1GitHubInput from './components/Step1GitHubInput'
import Step2Suggestions from './components/Step2Suggestions'
import Step3VideoUpload from './components/Step3VideoUpload'
import Step4FinalVideo from './components/Step4FinalVideo'

function App() {
  const [step, setStep] = useState(1)
  const [sessionId, setSessionId] = useState(null)
  const [githubUrl, setGithubUrl] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [uploadedVideos, setUploadedVideos] = useState({})
  const [finalVideoUrl, setFinalVideoUrl] = useState(null)
  const [processingStatus, setProcessingStatus] = useState('idle')

  const handleGitHubSubmit = (url, session, suggestionsData) => {
    setGithubUrl(url)
    setSessionId(session)
    setSuggestions(suggestionsData)
    setStep(2)
  }

  const handleVideoUploaded = (suggestionId, videoUrl) => {
    setUploadedVideos(prev => {
      const updated = {
        ...prev,
        [suggestionId]: videoUrl
      }
      
      // Check if all videos are uploaded
      if (Object.keys(updated).length >= suggestions.length) {
        // Use setTimeout to ensure state is updated
        setTimeout(() => {
          setStep(4)
          setProcessingStatus('processing')
          // Start polling for final video
          pollForFinalVideo()
        }, 100)
      }
      
      return updated
    })
  }

  const pollForFinalVideo = () => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL || 'https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/prod'}/session/${sessionId}/status`)
        const data = await response.json()
        
        if (data.status === 'completed' && data.final_video_url) {
          setFinalVideoUrl(data.final_video_url)
          setProcessingStatus('completed')
          clearInterval(interval)
        } else if (data.status === 'failed') {
          setProcessingStatus('failed')
          clearInterval(interval)
        }
      } catch (error) {
        console.error('Error polling status:', error)
      }
    }, 3000) // Poll every 3 seconds

    // Stop polling after 5 minutes
    setTimeout(() => clearInterval(interval), 300000)
  }

  const handleStartOver = () => {
    setStep(1)
    setSessionId(null)
    setGithubUrl('')
    setSuggestions([])
    setUploadedVideos({})
    setFinalVideoUrl(null)
    setProcessingStatus('idle')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <header className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-2">
            AI Demo Builder
          </h1>
          <p className="text-xl text-gray-600">
            Transform your GitHub project into a polished demo video
          </p>
        </header>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-center space-x-4">
            {[1, 2, 3, 4].map((stepNum) => (
              <div key={stepNum} className="flex items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                    step >= stepNum
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-200 text-gray-500'
                  }`}
                >
                  {step > stepNum ? '✓' : stepNum}
                </div>
                {stepNum < 4 && (
                  <div
                    className={`w-16 h-1 ${
                      step > stepNum ? 'bg-primary-600' : 'bg-gray-200'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
          <div className="flex justify-center mt-4 space-x-16 text-sm text-gray-600">
            <span>GitHub Link</span>
            <span>AI Suggestions</span>
            <span>Upload Videos</span>
            <span>Final Video</span>
          </div>
        </div>

        {/* Step Content */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {step === 1 && (
            <Step1GitHubInput
              onSubmit={handleGitHubSubmit}
              initialUrl={githubUrl}
            />
          )}
          {step === 2 && (
            <Step2Suggestions
              suggestions={suggestions}
              onContinue={() => setStep(3)}
              onBack={() => setStep(1)}
            />
          )}
          {step === 3 && (
            <Step3VideoUpload
              sessionId={sessionId}
              suggestions={suggestions}
              uploadedVideos={uploadedVideos}
              onVideoUploaded={handleVideoUploaded}
              onBack={() => setStep(2)}
            />
          )}
          {step === 4 && (
            <Step4FinalVideo
              finalVideoUrl={finalVideoUrl}
              processingStatus={processingStatus}
              onStartOver={handleStartOver}
            />
          )}
        </div>
      </div>
    </div>
  )
}

export default App

