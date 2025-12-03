import { useState } from 'react'
import Step1GitHubInput from './components/Step1GitHubInput'
import Step2SuggestionsWithUpload from './components/Step2SuggestionsWithUpload' // Combined component
import Step3FinalVideo from './components/Step3FinalVideo' // Was Step4, now Step3

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
    setStep(2) // Go to combined suggestions + upload step
  }

  const handleAllVideosUploaded = (videos) => {
    setUploadedVideos(videos)
    setStep(3) // Go to final video processing
    setProcessingStatus('processing')
    pollForFinalVideo()
  }

  const pollForFinalVideo = () => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_URL}/session/${sessionId}/status`
        )
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
    }, 3000)

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
      <div className="container mx-auto px-4 py-8 max-w-5xl">
        <header className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-2">
            AI Demo Builder
          </h1>
          <p className="text-xl text-gray-600">
            Transform your GitHub project into a polished demo video
          </p>
        </header>

        {/* Simplified Progress Steps (Now only 3 steps) */}
        <div className="mb-8">
          <div className="flex items-center justify-center space-x-4">
            {[
              { num: 1, label: 'GitHub URL' },
              { num: 2, label: 'Record Videos' },
              { num: 3, label: 'Final Demo' }
            ].map((stepItem) => (
              <div key={stepItem.num} className="flex items-center">
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center font-semibold text-lg ${
                    step >= stepItem.num
                      ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                      : 'bg-gray-200 text-gray-500'
                  }`}
                >
                  {step > stepItem.num ? '✓' : stepItem.num}
                </div>
                {stepItem.num < 3 && (
                  <div
                    className={`w-20 h-1 ${
                      step > stepItem.num 
                        ? 'bg-gradient-to-r from-blue-500 to-purple-600' 
                        : 'bg-gray-200'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
          <div className="flex justify-center mt-4 space-x-12 text-sm text-gray-600">
            <span>Submit Project</span>
            <span>Upload Clips</span>
            <span>Get Demo</span>
          </div>
        </div>

        {/* Step Content */}
        <div className="bg-white rounded-2xl shadow-xl">
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
      </div>
    </div>
  )
}

export default App