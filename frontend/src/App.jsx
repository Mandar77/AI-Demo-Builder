import { useState } from 'react'
import Step1GitHubInput from './components/Step1GitHubInput'
import Step1AnalysisResults from './components/Step1AnalysisResults'
import Step2Suggestions from './components/Step2Suggestions'
import Step3VideoUpload from './components/Step2SuggestionsWithUpload' // Upload component
import Step4FinalVideo from './components/Step3FinalVideo'

function App() {
  const [step, setStep] = useState(1)
  const [sessionId, setSessionId] = useState(null)
  const [githubUrl, setGithubUrl] = useState('')
  const [analysisData, setAnalysisData] = useState(null)
  const [suggestions, setSuggestions] = useState([])
  const [uploadedVideos, setUploadedVideos] = useState({})
  const [finalVideoUrl, setFinalVideoUrl] = useState(null)
  const [processingStatus, setProcessingStatus] = useState('idle')
  const [statusData, setStatusData] = useState(null) // Store full status response

  const handleGitHubSubmit = (url, session, suggestionsData, analysisData) => {
    setGithubUrl(url)
    setSessionId(session)
    setSuggestions(suggestionsData)
    setAnalysisData(analysisData)
    setStep(1.5) // Show analysis results first
  }

  const handleContinueToSuggestions = () => {
    setStep(2) // Go to suggestions display step
  }

  const handleContinueToUpload = () => {
    setStep(3) // Go to upload step
  }

  const handleAllVideosUploaded = (videos) => {
    setUploadedVideos(videos)
    setStep(4) // Go to final video processing
    setProcessingStatus('processing')
    pollForFinalVideo()
  }

  const pollForFinalVideo = () => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_URL}/session/${sessionId}/status`
        )
        const responseData = await response.json()
        
        // Handle different response formats
        // Status Tracker returns: { session_id, status, progress: {...}, ... }
        // API Gateway might wrap it or return directly
        const data = responseData.data || responseData
        
        // Store full status data for display
        setStatusData(data)
        
        // Extract status and demo URL
        const status = data.status || 'processing'
        const demoUrl = data.demo_url || data.final_video_url
        
        if (status === 'complete' || status === 'completed') {
          if (demoUrl) {
            setFinalVideoUrl(demoUrl)
            setProcessingStatus('completed')
            clearInterval(interval)
          } else {
            // Still processing, show progress
            setProcessingStatus('processing')
          }
        } else if (status === 'failed') {
          setProcessingStatus('failed')
          clearInterval(interval)
        } else {
          // Still processing, show progress
          setProcessingStatus('processing')
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
    setAnalysisData(null)
    setSuggestions([])
    setUploadedVideos({})
    setFinalVideoUrl(null)
    setProcessingStatus('idle')
    setStatusData(null)
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

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-center space-x-4">
            {[
              { num: 1, label: 'GitHub URL' },
              { num: 2, label: 'AI Suggestions' },
              { num: 3, label: 'Upload Clips' },
              { num: 4, label: 'Final Demo' }
            ].map((stepItem) => {
              let isCompleted = false
              let isActive = false
              let lineColored = false
              
              if (stepItem.num === 1) {
                // Step 1 is completed when at step 1.5 or beyond
                isCompleted = step === 1.5 || step >= 2
                isActive = step === 1
                // Line after step 1 is colored when step 1 is completed
                lineColored = step === 1.5 || step >= 2
              } else if (stepItem.num === 2) {
                // Step 2 is completed when at step 3 or beyond
                isCompleted = step >= 3
                // Step 2 is active only when at step 2 (not at step 1.5)
                isActive = step === 2
                // Line after step 2 is colored when step 2 is completed
                lineColored = step >= 3
              } else if (stepItem.num === 3) {
                // Step 3 is completed when at step 4 or beyond
                isCompleted = step >= 4
                // Step 3 is active when at step 3
                isActive = step === 3
                // Line after step 3 is colored when step 3 is completed
                lineColored = step >= 4
              } else if (stepItem.num === 4) {
                // Step 4 is active when at step 4
                isActive = step === 4
              }
              
              const shouldHighlight = isCompleted || isActive
              const showCheckmark = isCompleted
              
              return (
                <div key={stepItem.num} className="flex items-center">
                  <div
                    className={`w-12 h-12 rounded-full flex items-center justify-center font-semibold text-lg ${
                      shouldHighlight
                        ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                        : 'bg-gray-200 text-gray-500'
                    }`}
                  >
                    {showCheckmark ? '✓' : stepItem.num}
                  </div>
                  {stepItem.num < 4 && (
                    <div
                      className={`w-20 h-1 ${
                        lineColored
                          ? 'bg-gradient-to-r from-blue-500 to-purple-600' 
                          : 'bg-gray-200'
                      }`}
                    />
                  )}
                </div>
              )
            })}
          </div>
          <div className="flex justify-center mt-4 space-x-8 text-sm text-gray-600">
            <span>{step === 1 ? 'Submit Project' : step === 1.5 ? 'Review Analysis' : '✓ Submit Project'}</span>
            <span>{step >= 2 ? (step > 2 ? '✓ AI Suggestions' : 'AI Suggestions') : 'AI Suggestions'}</span>
            <span>{step >= 3 ? (step > 3 ? '✓ Upload Clips' : 'Upload Clips') : 'Upload Clips'}</span>
            <span>{step >= 4 ? 'Get Demo' : 'Get Demo'}</span>
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

          {step === 1.5 && analysisData && (
            <div className="p-8">
              <Step1AnalysisResults
                analysisData={analysisData}
                githubUrl={githubUrl}
                onContinue={handleContinueToSuggestions}
                onBack={() => setStep(1)}
              />
            </div>
          )}
          
          {step === 2 && (
            <Step2Suggestions
              suggestions={suggestions}
              onContinue={handleContinueToUpload}
              onBack={() => setStep(1.5)}
            />
          )}
          
          {step === 3 && (
            <Step3VideoUpload
              sessionId={sessionId}
              suggestions={suggestions}
              onAllVideosUploaded={handleAllVideosUploaded}
              onBack={() => setStep(2)}
            />
          )}
          
          {step === 4 && (
            <div className="p-8">
              <Step4FinalVideo
                finalVideoUrl={finalVideoUrl}
                processingStatus={processingStatus}
                statusData={statusData}
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