import React, { useState } from 'react';
import { Upload, Video, CheckCircle, AlertCircle, Loader, ArrowLeft } from 'lucide-react';
import api from '../services/api';

function Step2SuggestionsWithUpload({ sessionId, suggestions = [], onAllVideosUploaded, onBack }) {
  const [uploadedVideos, setUploadedVideos] = useState({});
  const [uploading, setUploading] = useState({});
  const [uploadProgress, setUploadProgress] = useState({});
  const [errors, setErrors] = useState({});

  const handleFileSelect = async (suggestion, index) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'video/*';
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      // Validate file
      if (!file.type.startsWith('video/')) {
        setErrors(prev => ({
          ...prev,
          [index]: 'Please select a video file'
        }));
        return;
      }

      if (file.size > 100 * 1024 * 1024) {
        setErrors(prev => ({
          ...prev,
          [index]: 'File size must be less than 100MB'
        }));
        return;
      }

      await uploadVideo(suggestion, index, file);
    };
    input.click();
  };

  const uploadVideo = async (suggestion, index, file) => {
    const suggestionId = (index + 1).toString();
    setUploading(prev => ({ ...prev, [suggestionId]: true }));
    setErrors(prev => ({ ...prev, [suggestionId]: null }));
    setUploadProgress(prev => ({ ...prev, [suggestionId]: 0 }));

    try {
      // Get presigned upload URL
      const urlResponse = await api.getUploadUrl(sessionId, suggestionId, file.name);
      const uploadUrl = urlResponse.upload_url;

      // Upload to S3 using XMLHttpRequest for progress tracking
      await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const percentComplete = Math.round((e.loaded / e.total) * 100);
            setUploadProgress(prev => ({
              ...prev,
              [suggestionId]: percentComplete
            }));
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status === 200) {
            resolve();
          } else {
            reject(new Error(`Upload failed with status ${xhr.status}`));
          }
        });

        xhr.addEventListener('error', () => reject(new Error('Upload failed')));
        xhr.addEventListener('abort', () => reject(new Error('Upload aborted')));

        xhr.open('PUT', uploadUrl);
        xhr.setRequestHeader('Content-Type', 'video/mp4');
        xhr.send(file);
      });

      // Mark as uploaded
      const newUploadedVideos = {
        ...uploadedVideos,
        [suggestionId]: file.name
      };
      setUploadedVideos(newUploadedVideos);
      setUploadProgress(prev => ({ ...prev, [suggestionId]: 100 }));

      // Check if all videos are uploaded
      if (Object.keys(newUploadedVideos).length === suggestions.length) {
        setTimeout(() => onAllVideosUploaded(newUploadedVideos), 500);
      }

    } catch (error) {
      console.error('Upload error:', error);
      setErrors(prev => ({
        ...prev,
        [suggestionId]: error.message || 'Failed to upload video'
      }));
    } finally {
      setUploading(prev => ({ ...prev, [suggestionId]: false }));
    }
  };

  const uploadedCount = Object.keys(uploadedVideos).length;
  const progress = suggestions.length > 0 ? (uploadedCount / suggestions.length) * 100 : 0;

  if (!suggestions || suggestions.length === 0) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-500">No suggestions available. Please go back and try again.</p>
        <button onClick={onBack} className="mt-4 btn-secondary">
          <ArrowLeft className="w-5 h-5 mr-2" />
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-3">
          Step 2: Record Your Demo Videos
        </h2>
        <p className="text-gray-600 mb-6">
          Follow each AI suggestion and upload your recorded video clips
        </p>

        {/* Progress Bar */}
        <div className="max-w-md mx-auto">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>{uploadedCount} of {suggestions.length} videos uploaded</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-gradient-to-r from-blue-500 to-purple-600 h-3 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      {/* Suggestions with Upload */}
      <div className="space-y-4 mb-8">
        {suggestions.map((suggestion, index) => {
          const suggestionId = (index + 1).toString();
          const isUploaded = !!uploadedVideos[suggestionId];
          const isUploading = uploading[suggestionId];
          const uploadProg = uploadProgress[suggestionId] || 0;
          const error = errors[suggestionId];

          return (
            <div
              key={index}
              className={`relative rounded-xl border-2 transition-all duration-300 ${isUploaded
                  ? 'bg-green-50 border-green-300 shadow-lg'
                  : isUploading
                    ? 'bg-blue-50 border-blue-300 shadow-md'
                    : 'bg-white border-gray-200 hover:shadow-md'
                }`}
            >
              <div className="p-6">
                {/* Suggestion Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start flex-1">
                    <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        {suggestion.title || `Video Segment ${index + 1}`}
                      </h3>

                      <p> <span className="text-md font-semibold text-gray-900 mb-2">Video Type: </span>{suggestion.video_type}</p>
                      <br></br>

                      <h4 className="text-md font-semibold text-gray-900 mb-2">Video Recording Instructions: </h4>
                      <div>
                        {suggestion.what_to_record && suggestion.what_to_record.length > 0 ? (
                          suggestion.what_to_record.map((idea, idx) => (
                            <p key={idx}> {idx + 1}. {idea}</p>
                          ))
                        ) : (
                          <p className="text-gray-500 italic">No recording instructions available.</p>
                        )}
                      </div>
                      <br></br>
                      {suggestion.key_highlights && (
                        <>
                          <h4 className="text-md font-semibold text-gray-900 mb-2">Key Highlights: </h4>
                          <div>
                            {suggestion.key_highlights && suggestion.key_highlights.length > 0 ? (
                              suggestion.key_highlights.map((idea, idx) => (
                                <p key={idx}> {idx + 1}. {idea}</p>
                              ))
                            ) : (
                              <p className="text-gray-500 italic">No key highlights instructions available.</p>
                            )}
                          </div>
                        </>
                      )}
                      <br></br>

                      {suggestion.narration_script && (
                        <>
                        <h4 className="text-md font-semibold text-gray-900 mb-2">Example Narration Script: </h4>
                        <p className="text-sm text-gray-900 flex items-center"> {suggestion.narration_script}</p>
                        </>
                      )}
                      <br></br>

                      {suggestion.duration && (
                        <p className="text-sm text-gray-500 flex items-center">
                          <Video className="w-4 h-4 mr-1" />
                          Suggested duration: {suggestion.duration} seconds
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Status Icon */}
                  {isUploaded && (
                    <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0 ml-4" />
                  )}
                </div>

                {/* Upload Section */}
                <div className="ml-14 mt-4">
                  {isUploaded ? (
                    <div className="flex items-center text-green-700 bg-green-100 px-4 py-2 rounded-lg">
                      <CheckCircle className="w-5 h-5 mr-2" />
                      <span className="font-medium">Uploaded: {uploadedVideos[suggestionId]}</span>
                    </div>
                  ) : (
                    <div>
                      <button
                        onClick={() => handleFileSelect(suggestion, index)}
                        disabled={isUploading}
                        className={`
                          inline-flex items-center px-6 py-3 rounded-lg font-semibold
                          transition-all duration-200 transform hover:scale-105
                          ${isUploading
                            ? 'bg-gray-400 text-white cursor-not-allowed'
                            : 'bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700 shadow-md hover:shadow-lg'
                          }
                        `}
                      >
                        {isUploading ? (
                          <>
                            <Loader className="w-5 h-5 mr-2 animate-spin" />
                            Uploading...
                          </>
                        ) : (
                          <>
                            <Upload className="w-5 h-5 mr-2" />
                            Upload Video
                          </>
                        )}
                      </button>

                      {/* Upload Progress */}
                      {isUploading && (
                        <div className="mt-4">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                              style={{ width: `${uploadProg}%` }}
                            />
                          </div>
                          <p className="text-sm text-gray-600 mt-1">{uploadProg}% uploaded</p>
                        </div>
                      )}

                      {/* Error Message */}
                      {error && (
                        <div className="mt-2 flex items-center text-red-600">
                          <AlertCircle className="w-4 h-4 mr-1" />
                          <span className="text-sm">{error}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Action Buttons */}
      <div className="flex justify-between items-center">
        <button
          onClick={onBack}
          className="btn-secondary flex items-center"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          Back
        </button>

        {uploadedCount === suggestions.length && (
          <button
            onClick={() => onAllVideosUploaded(uploadedVideos)}
            className="btn-primary flex items-center animate-pulse-slow"
          >
            Process Videos
            <ArrowRight className="w-5 h-5 ml-2" />
          </button>
        )}
      </div>
    </div>
  );
}

export default Step2SuggestionsWithUpload;