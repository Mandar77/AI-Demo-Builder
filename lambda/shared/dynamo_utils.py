"""
DynamoDB utility functions for Lambda functions
"""
import boto3
import os
import json
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'Sessions')
table = dynamodb.Table(TABLE_NAME)


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert Decimal to int/float for JSON serialization"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def get_session(session_id):
    """
    Get a session from DynamoDB
    
    Args:
        session_id: Session ID
    
    Returns:
        dict: Session data or None if not found
    """
    try:
        response = table.get_item(Key={'id': session_id})
        if 'Item' in response:
            return response['Item']
        return None
    except ClientError as e:
        print(f"Error getting session: {e}")
        raise


def create_session(session_id, github_url, project_name=None, status='initialized'):
    """
    Create a new session in DynamoDB
    
    Args:
        session_id: Session ID
        github_url: GitHub repository URL
        project_name: Project name (optional)
        status: Initial status
    
    Returns:
        dict: Created session data
    """
    try:
        now = datetime.utcnow()
        expires_at = int((now + timedelta(days=30)).timestamp())
        
        item = {
            'id': session_id,
            'github_url': github_url,
            'project_name': project_name or '',
            'status': status,
            'suggestions': [],
            'uploaded_videos': {},
            'demo_url': '',
            'created_at': now.isoformat(),
            'expires_at': expires_at
        }
        
        table.put_item(Item=item)
        return item
    except ClientError as e:
        print(f"Error creating session: {e}")
        raise


def update_session(session_id, **updates):
    """
    Update session fields in DynamoDB
    
    Args:
        session_id: Session ID
        **updates: Fields to update
    
    Returns:
        dict: Updated session data
    """
    try:
        update_expression_parts = []
        expression_attribute_names = {}
        expression_attribute_values = {}
        
        for key, value in updates.items():
            update_expression_parts.append(f"#{key} = :{key}")
            expression_attribute_names[f"#{key}"] = key
            expression_attribute_values[f":{key}"] = value
        
        update_expression = "SET " + ", ".join(update_expression_parts)
        
        response = table.update_item(
            Key={'id': session_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )
        
        return response['Attributes']
    except ClientError as e:
        print(f"Error updating session: {e}")
        raise


def update_session_status(session_id, status):
    """
    Update session status
    
    Args:
        session_id: Session ID
        status: New status
    """
    return update_session(session_id, status=status)


def add_suggestions(session_id, suggestions):
    """
    Add suggestions to session
    
    Args:
        session_id: Session ID
        suggestions: List of suggestions
    """
    return update_session(session_id, suggestions=suggestions)


def add_uploaded_video(session_id, video_id, s3_key):
    """
    Add uploaded video to session
    
    Args:
        session_id: Session ID
        video_id: Video ID (suggestion ID)
        s3_key: S3 key of uploaded video
    """
    session = get_session(session_id)
    if session:
        uploaded_videos = session.get('uploaded_videos', {})
        uploaded_videos[video_id] = s3_key
        return update_session(session_id, uploaded_videos=uploaded_videos)
    return None


def set_demo_url(session_id, demo_url):
    """
    Set final demo URL for session
    
    Args:
        session_id: Session ID
        demo_url: Final demo video URL
    """
    return update_session(session_id, demo_url=demo_url, status='complete')


def delete_session(session_id):
    """
    Delete a session from DynamoDB
    
    Args:
        session_id: Session ID
    """
    try:
        table.delete_item(Key={'id': session_id})
    except ClientError as e:
        print(f"Error deleting session: {e}")
        raise

