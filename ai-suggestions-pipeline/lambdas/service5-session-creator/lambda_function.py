import json
import os
import boto3
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
SESSIONS_TABLE_NAME = os.environ.get('SESSIONS_TABLE_NAME', 'ai-demo-sessions')

def lambda_handler(event, context):
    """
    Service 5: Session Manager
    Single Responsibility: Store Session Data in DynamoDB
    """
    try:
        print("[Service 5] Starting Session Manager")
        print(f"[Service 5] Table: {SESSIONS_TABLE_NAME}")

        # Extract data from Service 4
        session_id = event.get('session_id')
        github_data = event.get('github_data', {})
        suggestions = event.get('suggestions', {})
        
        # Validate required fields
        if not session_id:
            raise ValueError("session_id is required")

        if not github_data:
            raise ValueError("github_data is required")
        
        # Extract project details
        project_name = github_data.get('projectName', 'Unknown')
        owner = github_data.get('owner', 'unknown')
        github_url = f"https://github.com/{owner}/{project_name}"

        if not project_name or project_name == 'Unknown':
            raise ValueError("projectName is required in github_data")

        print(f"[Service 5] Session: {session_id}")
        print(f"[Service 5] Project: {project_name}")

        # Create timestamps
        now = datetime.utcnow()
        created_at = now.isoformat() + 'Z'
        updated_at = created_at
        
        # Set expiration (30 days from now)
        expires_at = int((now + timedelta(days=30)).timestamp())

        # Transform suggestions to match expected format
        transformed_suggestions = []
        videos = suggestions.get('videos', [])
        
        for idx, video in enumerate(videos, 1):
            transformed_suggestions.append({
                'id': f"suggestion_{idx}",
                'sequence_number': video.get('sequence_number', idx),
                'title': video.get('title', ''),
                'description': video.get('description', ''),
                'duration': parse_duration_to_seconds(video.get('duration', '1 minute')),
                'video_type': video.get('video_type', 'feature_demo'),
                'what_to_record': video.get('what_to_record', []),
                'narration_script': video.get('narration_script', ''),
                'key_highlights': video.get('key_highlights', []),
                'technical_setup': video.get('technical_setup', {}),
                'expected_outcome': video.get('expected_outcome', ''),
                'transition_to_next': video.get('transition_to_next', '')
            })

        # Create session item matching expected schema
        session_item = {
            'id': session_id,              # Primary identifier (using session_id as id)
            'project_name': project_name,  # Partition key
            'session_id': session_id,      # Sort key (keeping both for compatibility)
            'github_url': github_url,
            'status': 'initialized',
            'suggestions': transformed_suggestions,
            'uploaded_videos': {},         # Empty dict - videos uploaded later
            'created_at': created_at,
            'updated_at': updated_at,
            'expires_at': expires_at,
            # Additional fields for reference
            'owner': owner,
            'github_data': github_data,
            'project_analysis': event.get('project_analysis', {}),
            'project_metadata': event.get('project_metadata', {})
        }

        # Store in DynamoDB
        print(f"[Service 5] Storing session in DynamoDB...")
        table = dynamodb.Table(SESSIONS_TABLE_NAME)
        
        response = table.put_item(Item=session_item)
        
        print(f"[Service 5] ✅ Session stored successfully")
        print(f"[Service 5] HTTPStatusCode: {response['ResponseMetadata']['HTTPStatusCode']}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'id': session_id,
                'session_id': session_id,
                'project_name': project_name,
                'status': 'stored',
                'table': SESSIONS_TABLE_NAME,
                'created_at': created_at
            })
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"[Service 5] ❌ DynamoDB ClientError ({error_code}): {str(e)}")
        print(f"[Service 5] Error Message: {e.response['Error']['Message']}")
        raise
        
    except Exception as e:
        print(f"[Service 5] ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def parse_duration_to_seconds(duration_str):
    """
    Convert duration string to seconds
    Examples: '1.5 minutes' -> 90, '2 minutes' -> 120, '1 minute' -> 60
    """
    try:
        duration_str = duration_str.lower().strip()
        
        # Extract number
        import re
        numbers = re.findall(r'[\d.]+', duration_str)
        
        if not numbers:
            return 60  # Default 1 minute
        
        value = float(numbers[0])
        
        # Convert to seconds
        if 'minute' in duration_str:
            return int(value * 60)
        elif 'second' in duration_str:
            return int(value)
        elif 'hour' in duration_str:
            return int(value * 3600)
        else:
            return int(value * 60)  # Default to minutes
            
    except Exception as e:
        print(f"[Service 5] ⚠️ Could not parse duration '{duration_str}': {e}")
        return 60  # Default 1 minute