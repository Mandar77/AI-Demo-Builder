import { useState } from 'react'
import { api } from '../services/api'

function Step3VideoUpload({ sessionId, suggestions, uploadedVideos, onVideoUploaded, onBack }) {
  const [uploading, setUploading] = useState({})
  const [uploadProgress, setUploadProgress] = useState({})
  const [errors, setErrors] = useState({})

  const handleFileSelect = async (suggestion, index) => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'video/mp4,video/*'
    input.onchange = async (e) => {
      const file = e.target.files[0]
      if (!file) return

      // Validate file type
      if (!file.type.startsWith('video/')) {
        setErrors(prev => ({
          ...prev,
          [suggestion.id || index]: 'Please select a video file'
        }))
        return
      }

      // Validate file size (max 100MB)
      if (file.size > 100 * 1024 * 1024) {
        setErrors(prev => ({
          ...prev,
          [suggestion.id || index]: 'File size must be less than 100MB'
        }))
        return
      }

      await uploadVideo(suggestion, index, file)
    }
    input.click()
  }

  const uploadVideo = async (suggestion, index, file) => {
    const suggestionId = suggestion.id || index.toString()
    setUploading(prev => ({ ...prev, [suggestionId]: true }))
    setErrors(prev => ({ ...prev, [suggestionId]: null }))
    setUploadProgress(prev => ({ ...prev, [suggestionId]: 0 }))

    try {
      // Get presigned upload URL
      const uploadUrl = await api.getUploadUrl(sessionId, suggestionId)

      // Upload to S3 using XMLHttpRequest for progress tracking
      await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest()

        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100
            setUploadProgress(prev => ({
              ...prev,
              [suggestionId]: Math.round(percentComplete)
            }))
          }
        })

        xhr.addEventListener('load', () => {
          if (xhr.status === 200) {
            resolve()
          } else {
            reject(new Error('Upload failed'))
          }
        })

        xhr.addEventListener('error', () => reject(new Error('Upload failed')))
        xhr.addEventListener('abort', () => reject(new Error('Upload aborted')))

        xhr.open('PUT', uploadUrl)
        xhr.setRequestHeader('Content-Type', 'video/mp4')
        xhr.send(file)
      })

      // Create a preview URL for the uploaded video
      const previewUrl = URL.createObjectURL(file)
      onVideoUploaded(suggestionId, previewUrl)

      setUploadProgress(prev => ({ ...prev, [suggestionId]: 100 }))
    } catch (error) {
      console.error('Upload error:', error)
      setErrors(prev => ({
        ...prev,
        [suggestionId]: error.message || 'Failed to upload video. Please try again.'
      }))
    } finally {
      setUploading(prev => ({ ...prev, [suggestionId]: false }))
    }
  }

  const allUploaded = suggestions.every((s, i) => {
    const id = s.id || i.toString()
    return uploadedVideos[id]
  })

  return (
    <div className="max-w-3xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-3">
          Step 3: Upload Your Videos
        </h2>
        <p className="text-gray-600">
          Upload {suggestions.length} short video clips following the suggestions above.
        </p>
      </div>

      <div className="space-y-6 mb-8">
        {suggestions.map((suggestion, index) => {
          const suggestionId = suggestion.id || index.toString()
          const isUploaded = !!uploadedVideos[suggestionId]
          const isUploading = uploading[suggestionId]
          const progress = uploadProgress[suggestionId] || 0
          const error = errors[suggestionId]

          return (
            <div
              key={suggestionId}
              className={`p-6 rounded-xl border-2 transition-all ${
                isUploaded
                  ? 'bg-green-50 border-green-300'
                  : isUploading
                  ? 'bg-blue-50 border-blue-300'
                  : 'bg-gray-50 border-gray-200'
              }`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <span className="w-8 h-8 bg-primary-600 text-white rounded-full flex items-center justify-center font-bold mr-3">
                      {index + 1}
                    </span>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {suggestion.title || `Video ${index + 1}`}
                    </h3>
                  </div>
                  <p className="text-gray-700 ml-11">
                    {suggestion.description || suggestion.text || suggestion}
                  </p>
                </div>
              </div>

              {isUploaded ? (
                <div className="ml-11 flex items-center text-green-700">
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="font-medium">Uploaded successfully!</span>
                </div>
              ) : (
                <div className="ml-11">
                  <button
                    onClick={() => handleFileSelect(suggestion, index)}
                    disabled={isUploading}
                    className="px-6 py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isUploading ? 'Uploading...' : 'Select Video'}
                  </button>

                  {isUploading && (
                    <div className="mt-4">
                      <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div
                          className="bg-primary-600 h-2.5 rounded-full transition-all duration-300"
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{progress}% uploaded</p>
                    </div>
                  )}

                  {error && (
                    <p className="mt-2 text-sm text-red-600">{error}</p>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      <div className="flex justify-between">
        <button
          onClick={onBack}
          className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
        >
          Back
        </button>
        {allUploaded && (
          <div className="text-green-600 font-medium flex items-center">
            <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            All videos uploaded! Processing...
          </div>
        )}
      </div>
    </div>
  )
}

export default Step3VideoUpload

