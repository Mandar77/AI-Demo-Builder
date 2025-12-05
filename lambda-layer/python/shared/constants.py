"""
This file contains Runtime Constants for Lambda Functions
"""
GITHUB_REPO_ANALYSIS_API_URL = 'https://dez4stbz65.execute-api.us-west-1.amazonaws.com/prod/analyze'
GITHUB_REPO_ANALYSIS_API_TIMEOUT = 30

class Status:
    """Session status values"""
    INITIALIZED = 'initialized'
    GENERATING_SUGGESTIONS = 'generating_suggestions'
    SUGGESTIONS_READY = 'suggestions_ready'
    Error = 'error'

class VideoStatus:
    """Individual video status"""
    PENDING = 'pending'
    UPLOADED = 'uploaded'
    COMPLETE = 'complete'
    ERROR = 'error'

