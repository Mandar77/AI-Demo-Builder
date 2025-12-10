import json
import os
import boto3
import subprocess
import tempfile
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

BUCKET = os.environ.get('S3_BUCKET', 'ai-demo-builder')
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'ai-demo-sessions')
MAX_DURATION = int(os.environ.get('MAX_VIDEO_DURATION', '120'))  # 2 minutes max
MIN_DURATION = int(os.environ.get('MIN_VIDEO_DURATION', '5'))    # 5 seconds min
MAX_FILE_SIZE = int(os.environ.get('MAX_FILE_SIZE', '104857600')) # 100MB

def handler(event, context):
    """
    Validate uploaded video files
    """
    print(f"Event: {json.dumps(event)}")
    
    try:
        body = json.loads(event['body'])
        session_id = body['session_id']
        suggestion_id = body['suggestion_id']
        s3_key = body['s3_key']
        
        # Download video to temp location
        temp_file = download_video(s3_key)
        
        # Validate video
        validation_result = validate_video(temp_file)
        
        # Update DynamoDB with validation results
        update_validation_status(session_id, suggestion_id, validation_result)
        
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        # If validation passed, trigger format conversion
        if validation_result['valid']:
            trigger_format_conversion(session_id, suggestion_id, s3_key)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'session_id': session_id,
                'suggestion_id': suggestion_id,
                'validation': validation_result
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }

def download_video(s3_key):
    """
    Download video from S3 to temp location
    """
    temp_file = tempfile.mktemp(suffix='.mp4')
    
    try:
        s3_client.download_file(BUCKET, s3_key, temp_file)
        print(f"Downloaded {s3_key} to {temp_file}")
        return temp_file
    except ClientError as e:
        print(f"Error downloading file: {e}")
        raise

def validate_video(file_path):
    """
    Validate video file using ffprobe
    """
    validation_result = {
        'valid': False,
        'errors': [],
        'warnings': [],
        'metadata': {}
    }
    
    try:
        # Check file size
        file_size = os.path.getsize(file_path)
        validation_result['metadata']['file_size'] = file_size
        
        if file_size > MAX_FILE_SIZE:
            validation_result['errors'].append(f"File size {file_size} exceeds maximum {MAX_FILE_SIZE}")
            return validation_result
        
        # Use ffprobe to get video metadata
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            validation_result['errors'].append("Failed to read video metadata")
            return validation_result
        
        metadata = json.loads(result.stdout)
        
        # Extract video stream info
        video_stream = None
        for stream in metadata.get('streams', []):
            if stream['codec_type'] == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            validation_result['errors'].append("No video stream found")
            return validation_result
        
        # Get video properties
        duration = float(metadata['format'].get('duration', 0))
        width = int(video_stream.get('width', 0))
        height = int(video_stream.get('height', 0))
        codec = video_stream.get('codec_name', 'unknown')
        fps = eval(video_stream.get('r_frame_rate', '0/1'))
        if isinstance(fps, tuple) and fps[1] != 0:
            fps = fps[0] / fps[1]
        else:
            fps = 0
        
        validation_result['metadata'].update({
            'duration': duration,
            'width': width,
            'height': height,
            'codec': codec,
            'fps': fps,
            'format': metadata['format'].get('format_name', 'unknown')
        })
        
        # Validation checks
        if duration < MIN_DURATION:
            validation_result['errors'].append(f"Video too short: {duration}s (minimum {MIN_DURATION}s)")
        elif duration > MAX_DURATION:
            validation_result['errors'].append(f"Video too long: {duration}s (maximum {MAX_DURATION}s)")
        
        if width < 320 or height < 240:
            validation_result['warnings'].append(f"Low resolution: {width}x{height}")
        
        if width > 3840 or height > 2160:
            validation_result['warnings'].append(f"Very high resolution: {width}x{height}")
        
        if codec not in ['h264', 'hevc', 'vp9', 'av1']:
            validation_result['warnings'].append(f"Non-standard codec: {codec}")
        
        # If no errors, mark as valid
        if not validation_result['errors']:
            validation_result['valid'] = True
        
    except Exception as e:
        validation_result['errors'].append(f"Validation error: {str(e)}")
    
    return validation_result

def update_validation_status(session_id, suggestion_id, validation_result):
    """
    Update DynamoDB with validation results
    """
    table = dynamodb.Table(TABLE_NAME)
    
    update_expression = 'SET #uploads.#suggId.#validation = :val'
    expression_names = {
        '#uploads': 'uploaded_videos',
        '#suggId': f'suggestion_{suggestion_id}',
        '#validation': 'validation'
    }
    expression_values = {
        ':val': validation_result
    }
    
    if validation_result['valid']:
        update_expression += ', #uploads.#suggId.#status = :status'
        expression_values[':status'] = 'validated'
    else:
        update_expression += ', #uploads.#suggId.#status = :status'
        expression_values[':status'] = 'validation_failed'
    
    try:
        table.update_item(
            Key={'id': session_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_names,
            ExpressionAttributeValues=expression_values
        )
        print(f"Updated validation status for session {session_id}, suggestion {suggestion_id}")
    except Exception as e:
        print(f"Error updating validation status: {e}")
        raise

def trigger_format_conversion(session_id, suggestion_id, s3_key):
    """
    Trigger the format converter Lambda
    """
    print(f"Triggering format conversion for {s3_key}")
    # In production, you would invoke the format-converter Lambda here
    # lambda_client = boto3.client('lambda')
    # lambda_client.invoke(
    #     FunctionName='format-converter',
    #     InvocationType='Event',
    #     Payload=json.dumps({
    #         'session_id': session_id,
    #         'suggestion_id': suggestion_id,
    #         's3_key': s3_key
    #     })
    # )