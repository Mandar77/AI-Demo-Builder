"""
Service 18: Cleanup Service
Removes expired sessions and associated S3 objects
"""
import json
import os
import boto3
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))

from s3_utils import list_files, delete_file
from dynamo_utils import delete_session, get_session
from error_handler import success_response, error_response, handle_lambda_error

dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'Sessions')
BUCKET_NAME = os.environ.get('S3_BUCKET', 'cs6620-ai-demo-builder')
table = dynamodb.Table(TABLE_NAME)


@handle_lambda_error
def lambda_handler(event, context):
    """
    Lambda handler for cleanup service
    
    Can be triggered by:
    1. CloudWatch Events (scheduled - daily)
    2. Direct API call
    """
    print(f"Received event: {json.dumps(event)}")
    
    # Get expiration threshold (default: 30 days ago)
    days_to_keep = int(os.environ.get('DAYS_TO_KEEP', '30'))
    threshold_timestamp = int((datetime.utcnow() - timedelta(days=days_to_keep)).timestamp())
    
    cleaned_sessions = []
    cleaned_files = []
    errors = []
    
    try:
        # Scan DynamoDB for expired sessions
        # Note: In production, use DynamoDB TTL for automatic deletion
        # This service handles cleanup of associated S3 files
        
        # Get all sessions (in production, use pagination)
        response = table.scan()
        sessions = response.get('Items', [])
        
        for session in sessions:
            session_id = session.get('id')
            expires_at = session.get('expires_at', 0)
            
            # Check if session is expired
            if expires_at and expires_at < threshold_timestamp:
                try:
                    # Delete associated S3 files
                    session_files = cleanup_session_files(session_id)
                    cleaned_files.extend(session_files)
                    
                    # Delete session from DynamoDB
                    delete_session(session_id)
                    cleaned_sessions.append(session_id)
                    
                    print(f"Cleaned up session: {session_id}")
                
                except Exception as e:
                    error_msg = f"Error cleaning session {session_id}: {str(e)}"
                    print(error_msg)
                    errors.append(error_msg)
        
        result = {
            'message': 'Cleanup completed',
            'sessions_cleaned': len(cleaned_sessions),
            'files_cleaned': len(cleaned_files),
            'errors': errors if errors else None
        }
        
        return success_response(result)
    
    except Exception as e:
        print(f"Error in cleanup service: {e}")
        return error_response(f"Cleanup failed: {str(e)}", 500)


def cleanup_session_files(session_id):
    """
    Delete all S3 files associated with a session
    
    Args:
        session_id: Session ID
    
    Returns:
        list: List of deleted file keys
    """
    deleted_files = []
    
    try:
        # List all files with session prefix
        prefixes = [
            f'videos/{session_id}/',
            f'demos/{session_id}/',
            f'temp/{session_id}/'
        ]
        
        for prefix in prefixes:
            files = list_files(prefix)
            for file_key in files:
                try:
                    delete_file(file_key)
                    deleted_files.append(file_key)
                    print(f"Deleted S3 file: {file_key}")
                except Exception as e:
                    print(f"Error deleting file {file_key}: {e}")
    
    except Exception as e:
        print(f"Error listing session files: {e}")
    
    return deleted_files

