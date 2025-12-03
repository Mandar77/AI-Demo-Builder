import json
import os
import boto3
import subprocess
import tempfile
from pathlib import Path

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

BUCKET = os.environ.get('S3_BUCKET', 'cs6620-ai-demo-builder')
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'Sessions')
QUEUE_URL = os.environ.get('SQS_QUEUE_URL', '')

# Standard output format for all videos
OUTPUT_WIDTH = 1920
OUTPUT_HEIGHT = 1080
OUTPUT_FPS = 30
OUTPUT_BITRATE = '2M'
OUTPUT_CODEC = 'libx264'
OUTPUT_FORMAT = 'mp4'

def handler(event, context):
    """
    Convert video to standardized format for processing
    """
    print(f"Event: {json.dumps(event)}")
    
    try:
        body = json.loads(event['body'])
        session_id = body['session_id']
        suggestion_id = body['suggestion_id']
        input_s3_key = body['s3_key']
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        input_file = os.path.join(temp_dir, 'input.mp4')
        output_file = os.path.join(temp_dir, f'standardized.{OUTPUT_FORMAT}')
        
        try:
            # Download input video
            s3_client.download_file(BUCKET, input_s3_key, input_file)
            print(f"Downloaded {input_s3_key}")
            
            # Convert video
            conversion_result = convert_video(input_file, output_file)
            
            if conversion_result['success']:
                # Upload converted video
                output_s3_key = f'videos/{session_id}/standardized_{suggestion_id}.{OUTPUT_FORMAT}'
                s3_client.upload_file(
                    output_file,
                    BUCKET,
                    output_s3_key,
                    ExtraArgs={'ContentType': 'video/mp4'}
                )
                print(f"Uploaded standardized video to {output_s3_key}")
                
                # Update DynamoDB
                update_conversion_status(session_id, suggestion_id, output_s3_key, conversion_result)
                
                # Check if all videos are ready for stitching
                if check_all_videos_ready(session_id):
                    trigger_video_stitching(session_id)
                
                result = {
                    'success': True,
                    'session_id': session_id,
                    'suggestion_id': suggestion_id,
                    'standardized_key': output_s3_key,
                    'details': conversion_result
                }
            else:
                result = {
                    'success': False,
                    'error': conversion_result.get('error', 'Conversion failed')
                }
            
        finally:
            # Clean up temp files
            for file in [input_file, output_file]:
                if os.path.exists(file):
                    os.remove(file)
            os.rmdir(temp_dir)
        
        return {
            'statusCode': 200 if result['success'] else 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }

def convert_video(input_file, output_file):
    """
    Convert video to standardized format using ffmpeg
    """
    result = {
        'success': False,
        'input_file': input_file,
        'output_file': output_file
    }
    
    try:
        # Build ffmpeg command for standardization
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-c:v', OUTPUT_CODEC,
            '-preset', 'medium',
            '-crf', '23',
            '-vf', f'scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease,pad={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={OUTPUT_FPS}',
            '-b:v', OUTPUT_BITRATE,
            '-maxrate', OUTPUT_BITRATE,
            '-bufsize', '1M',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-ar', '44100',
            '-f', OUTPUT_FORMAT,
            '-movflags', '+faststart',
            '-y',  # Overwrite output file
            output_file
        ]
        
        print(f"Running ffmpeg command: {' '.join(cmd)}")
        
        # Run ffmpeg
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if process.returncode == 0 and os.path.exists(output_file):
            # Get output file info
            output_size = os.path.getsize(output_file)
            
            # Get duration and verify conversion
            probe_cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                output_file
            ]
            
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            if probe_result.returncode == 0:
                metadata = json.loads(probe_result.stdout)
                duration = float(metadata['format'].get('duration', 0))
                
                result.update({
                    'success': True,
                    'output_size': output_size,
                    'duration': duration,
                    'format': OUTPUT_FORMAT,
                    'resolution': f'{OUTPUT_WIDTH}x{OUTPUT_HEIGHT}',
                    'fps': OUTPUT_FPS,
                    'codec': OUTPUT_CODEC
                })
            else:
                result['success'] = True
                result['output_size'] = output_size
        else:
            result['error'] = f"FFmpeg failed: {process.stderr}"
            
    except subprocess.TimeoutExpired:
        result['error'] = "Video conversion timed out"
    except Exception as e:
        result['error'] = str(e)
    
    return result

def update_conversion_status(session_id, suggestion_id, output_key, conversion_result):
    """
    Update DynamoDB with conversion results
    """
    table = dynamodb.Table(TABLE_NAME)
    
    update_data = {
        'status': 'converted',
        'standardized_key': output_key,
        'conversion_timestamp': str(int(os.times().elapsed * 1000)),
        'conversion_details': conversion_result
    }
    
    try:
        table.update_item(
            Key={'id': session_id},
            UpdateExpression='SET #uploads.#suggId.#converted = :data',
            ExpressionAttributeNames={
                '#uploads': 'uploaded_videos',
                '#suggId': f'suggestion_{suggestion_id}',
                '#converted': 'converted_data'
            },
            ExpressionAttributeValues={
                ':data': update_data
            }
        )
        print(f"Updated conversion status for session {session_id}, suggestion {suggestion_id}")
    except Exception as e:
        print(f"Error updating conversion status: {e}")
        raise

def check_all_videos_ready(session_id):
    """
    Check if all videos for a session have been converted
    """
    table = dynamodb.Table(TABLE_NAME)
    
    try:
        response = table.get_item(Key={'id': session_id})
        if 'Item' not in response:
            return False
        
        item = response['Item']
        suggestions = item.get('suggestions', [])
        uploaded_videos = item.get('uploaded_videos', {})
        
        # Check if all suggestions have converted videos
        for i, suggestion in enumerate(suggestions):
            video_key = f'suggestion_{i+1}'
            if video_key not in uploaded_videos:
                return False
            
            video_data = uploaded_videos[video_key]
            if not video_data.get('converted_data'):
                return False
        
        return True
        
    except Exception as e:
        print(f"Error checking video readiness: {e}")
        return False

def trigger_video_stitching(session_id):
    """
    Send message to SQS to trigger video stitching
    """
    if not QUEUE_URL:
        print("No SQS queue configured, skipping trigger")
        return
    
    try:
        message = {
            'session_id': session_id,
            'action': 'stitch_videos',
            'timestamp': str(int(os.times().elapsed * 1000))
        }
        
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(message),
            MessageAttributes={
                'session_id': {'StringValue': session_id, 'DataType': 'String'}
            }
        )
        
        print(f"Triggered video stitching for session {session_id}")
        
    except Exception as e:
        print(f"Error triggering video stitching: {e}")