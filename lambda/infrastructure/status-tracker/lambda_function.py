"""
Service 17: Status Tracker
Provides real-time status of session processing
"""
import json
import os
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))

from dynamo_utils import get_session
from error_handler import success_response, error_response, handle_lambda_error


@handle_lambda_error
def lambda_handler(event, context):
    """
    Lambda handler for status tracker
    
    GET /session/{session_id}/status
    """
    print(f"Received event: {json.dumps(event)}")
    
    # Extract session_id from path parameters
    session_id = None
    if event.get('pathParameters'):
        session_id = event['pathParameters'].get('session_id')
    
    # Fallback: try query string
    if not session_id and event.get('queryStringParameters'):
        session_id = event['queryStringParameters'].get('session_id')
    
    # Fallback: try body
    if not session_id:
        body = event.get('body', '{}')
        if isinstance(body, str):
            body = json.loads(body)
        session_id = body.get('session_id')
    
    if not session_id:
        return error_response('session_id is required', 400)
    
    # Get session from DynamoDB
    session = get_session(session_id)
    
    if not session:
        return error_response('Session not found', 404)
    
    # Format response
    response_data = {
        'session_id': session_id,
        'status': session.get('status', 'unknown'),
        'github_url': session.get('github_url', ''),
        'project_name': session.get('project_name', ''),
        'suggestions_count': len(session.get('suggestions', [])),
        'uploaded_videos_count': len(session.get('uploaded_videos', {})),
        'demo_url': session.get('demo_url', ''),
        'created_at': session.get('created_at', ''),
        'progress': calculate_progress(session)
    }
    
    return success_response(response_data)


def calculate_progress(session):
    """
    Calculate processing progress percentage
    
    Args:
        session: Session data from DynamoDB
    
    Returns:
        dict: Progress information
    """
    status = session.get('status', 'unknown')
    suggestions = session.get('suggestions', [])
    uploaded_videos = session.get('uploaded_videos', {})
    
    total_videos = len(suggestions)
    uploaded_count = len(uploaded_videos)
    
    progress_map = {
        'initialized': 0,
        'generating_suggestions': 10,
        'suggestions_ready': 20,
        'uploading': 30,
        'processing': 80,
        'complete': 100,
        'failed': 0
    }
    
    base_progress = progress_map.get(status, 0)
    
    # If in uploading phase, calculate based on uploaded videos
    if status == 'uploading' and total_videos > 0:
        upload_progress = (uploaded_count / total_videos) * 50  # 30-80% range
        base_progress = 30 + upload_progress
    
    return {
        'percentage': base_progress,
        'status': status,
        'uploaded': uploaded_count,
        'total': total_videos,
        'message': get_status_message(status, uploaded_count, total_videos)
    }


def get_status_message(status, uploaded_count, total_videos):
    """
    Get human-readable status message
    
    Args:
        status: Current status
        uploaded_count: Number of uploaded videos
        total_videos: Total number of videos expected
    
    Returns:
        str: Status message
    """
    messages = {
        'initialized': 'Session initialized',
        'generating_suggestions': 'AI is analyzing your repository...',
        'suggestions_ready': 'Ready for video uploads',
        'uploading': f'Uploaded {uploaded_count} of {total_videos} videos',
        'processing': 'Stitching videos together...',
        'complete': 'Demo video is ready!',
        'failed': 'Processing failed. Please try again.'
    }
    
    return messages.get(status, 'Processing...')

