"""
Service 16: Notification Service
Sends notifications when demo video processing is complete
"""
import json
import os
import boto3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))

from dynamo_utils import get_session
from error_handler import success_response, error_response, handle_lambda_error

sns_client = boto3.client('sns')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')


@handle_lambda_error
def lambda_handler(event, context):
    """
    Lambda handler for notification service
    
    Event can come from:
    1. SNS trigger (when video processing completes)
    2. Direct API call
    3. DynamoDB stream (when session status changes to 'complete')
    """
    print(f"Received event: {json.dumps(event)}")
    
    # Handle different event sources
    if 'Records' in event:
        # DynamoDB Stream event
        for record in event['Records']:
            if record['eventName'] == 'MODIFY':
                new_image = record.get('dynamodb', {}).get('NewImage', {})
                old_image = record.get('dynamodb', {}).get('OldImage', {})
                
                old_status = old_image.get('status', {}).get('S', '')
                new_status = new_image.get('status', {}).get('S', '')
                
                # Send notification when status changes to 'complete'
                if old_status != 'complete' and new_status == 'complete':
                    session_id = new_image.get('id', {}).get('S', '')
                    demo_url = new_image.get('demo_url', {}).get('S', '')
                    send_notification(session_id, demo_url)
        
        return success_response({'message': 'Notifications processed'})
    
    # Direct API call
    body = json.loads(event.get('body', '{}'))
    session_id = body.get('session_id')
    
    if not session_id:
        return error_response('session_id is required', 400)
    
    session = get_session(session_id)
    if not session:
        return error_response('Session not found', 404)
    
    if session.get('status') == 'complete':
        demo_url = session.get('demo_url', '')
        send_notification(session_id, demo_url)
        return success_response({'message': 'Notification sent'})
    else:
        return success_response({'message': 'Session not ready for notification'})


def send_notification(session_id, demo_url):
    """
    Send notification via SNS
    
    Args:
        session_id: Session ID
        demo_url: Final demo video URL
    """
    try:
        message = {
            'session_id': session_id,
            'demo_url': demo_url,
            'message': f'Your demo video is ready! View it at: {demo_url}',
            'timestamp': json.dumps({'timestamp': 'now'})
        }
        
        if SNS_TOPIC_ARN:
            sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=json.dumps(message),
                Subject='Demo Video Ready'
            )
            print(f"Notification sent for session {session_id}")
        else:
            # If no SNS topic, just log (for local testing)
            print(f"Would send notification: {message}")
    
    except Exception as e:
        print(f"Error sending notification: {e}")
        # Don't fail the Lambda if notification fails
        pass

