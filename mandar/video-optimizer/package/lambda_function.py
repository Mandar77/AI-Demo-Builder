"""
Video Optimizer Service - UPDATED WITH STATUS TRACKING
Replace your entire lambda_function.py with this version
"""

import os
import json
import subprocess
import boto3
from datetime import datetime
import tempfile
import shutil

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Configuration
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'cs6620-ai-builder-project')
TABLE_NAME = os.environ.get('TABLE_NAME', 'ai-demo-sessions')
PARTITION_KEY = os.environ.get('PARTITION_KEY', 'project_name')
FFMPEG_PATH = os.environ.get('FFMPEG_PATH', '/opt/bin/ffmpeg')
FFPROBE_PATH = os.environ.get('FFPROBE_PATH', '/opt/bin/ffprobe')

# Output presets
PRESETS = {
    '1080p': {
        'width': 1920,
        'height': 1080,
        'bitrate': '5M',
        'maxrate': '6M',
        'bufsize': '10M',
        'crf': 23,
        'audio_bitrate': '192k'
    },
    '720p': {
        'width': 1280,
        'height': 720,
        'bitrate': '2.5M',
        'maxrate': '3M',
        'bufsize': '5M',
        'crf': 24,
        'audio_bitrate': '128k'
    },
    '480p': {
        'width': 854,
        'height': 480,
        'bitrate': '1M',
        'maxrate': '1.5M',
        'bufsize': '2M',
        'crf': 25,
        'audio_bitrate': '96k'
    }
}


def update_session_status(session_id, status, additional_data=None):
    """Update session status in DynamoDB for frontend tracking"""
    table = dynamodb.Table(TABLE_NAME)
    
    update_expr = 'SET #status = :status, updated_at = :now'
    expr_names = {'#status': 'status'}
    expr_values = {
        ':status': status,
        ':now': datetime.utcnow().isoformat()
    }
    
    if additional_data:
        for key, value in additional_data.items():
            # Convert floats to strings for DynamoDB
            if isinstance(value, float):
                value = str(value)
            # Handle nested dicts/lists by converting to JSON string if needed
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            update_expr += f', {key} = :{key}'
            expr_values[f':{key}'] = value
    
    try:
        table.update_item(
            Key={PARTITION_KEY: session_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values
        )
        print(f"Status updated: {session_id} -> {status}")
    except Exception as e:
        print(f"Warning: Could not update DynamoDB: {e}")


def get_video_info(video_path):
    """Get video information using ffprobe"""
    cmd = [
        FFPROBE_PATH,
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        video_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        info = json.loads(result.stdout)
        
        format_info = info.get('format', {})
        duration = float(format_info.get('duration', 0))
        file_size = int(format_info.get('size', 0))
        
        video_stream = None
        audio_stream = None
        for stream in info.get('streams', []):
            if stream['codec_type'] == 'video' and not video_stream:
                video_stream = stream
            elif stream['codec_type'] == 'audio' and not audio_stream:
                audio_stream = stream
        
        return {
            'duration': duration,
            'file_size': file_size,
            'width': video_stream.get('width', 1920) if video_stream else 1920,
            'height': video_stream.get('height', 1080) if video_stream else 1080,
            'fps': eval(video_stream.get('r_frame_rate', '30/1')) if video_stream else 30,
            'video_codec': video_stream.get('codec_name') if video_stream else None,
            'audio_codec': audio_stream.get('codec_name') if audio_stream else None,
            'has_audio': audio_stream is not None
        }
    except Exception as e:
        print(f"Error getting video info: {e}")
        return None


def download_from_s3(s3_key, local_path):
    """Download file from S3"""
    print(f"Downloading s3://{BUCKET_NAME}/{s3_key} to {local_path}")
    s3_client.download_file(BUCKET_NAME, s3_key, local_path)
    return local_path


def upload_to_s3(local_path, s3_key, content_type='video/mp4'):
    """Upload file to S3"""
    print(f"Uploading {local_path} to s3://{BUCKET_NAME}/{s3_key}")
    s3_client.upload_file(
        local_path,
        BUCKET_NAME,
        s3_key,
        ExtraArgs={'ContentType': content_type}
    )
    return f"s3://{BUCKET_NAME}/{s3_key}"


def generate_presigned_url(s3_key, expires_in=86400):
    """Generate presigned URL for download (24 hours default)"""
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=expires_in
        )
        return url
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        return None


def optimize_video(input_path, output_path, preset_name):
    """Encode video with specified preset"""
    preset = PRESETS.get(preset_name, PRESETS['1080p'])
    
    cmd = [
        FFMPEG_PATH,
        '-y',
        '-i', input_path,
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', str(preset['crf']),
        '-maxrate', preset['maxrate'],
        '-bufsize', preset['bufsize'],
        '-vf', f"scale={preset['width']}:{preset['height']}:force_original_aspect_ratio=decrease,pad={preset['width']}:{preset['height']}:(ow-iw)/2:(oh-ih)/2:black",
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', preset['audio_bitrate'],
        '-ar', '44100',
        '-ac', '2',
        '-movflags', '+faststart',
        '-brand', 'mp42',
        output_path
    ]
    
    print(f"Encoding {preset_name}: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    
    if result.returncode != 0:
        print(f"FFmpeg stderr: {result.stderr}")
        raise Exception(f"Failed to encode video ({preset_name}): {result.stderr}")
    
    return output_path


def generate_thumbnail(input_path, output_path, timestamp='00:00:01'):
    """Generate thumbnail image from video"""
    cmd = [
        FFMPEG_PATH,
        '-y',
        '-i', input_path,
        '-ss', timestamp,
        '-vframes', '1',
        '-vf', 'scale=640:360:force_original_aspect_ratio=decrease,pad=640:360:(ow-iw)/2:(oh-ih)/2:black',
        '-q:v', '2',
        output_path
    ]
    
    print(f"Generating thumbnail: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    if result.returncode != 0:
        print(f"Warning: Failed to generate thumbnail: {result.stderr}")
        return None
    
    return output_path


def process_request(event):
    """Main processing logic"""
    if isinstance(event.get('body'), str):
        body = json.loads(event['body'])
    elif event.get('body'):
        body = event['body']
    else:
        body = event
    
    # Support both project_name and session_id for compatibility
    session_id = body.get('project_name') or body.get('session_id')
    if not session_id:
        raise ValueError('project_name is required')
    
    input_key = body.get('input_key')
    if not input_key:
        raise ValueError('input_key is required')
    
    resolutions = body.get('resolutions', ['1080p', '720p'])
    generate_thumb = body.get('generate_thumbnail', True)
    
    print(f"Optimizing video for session {session_id}")
    print(f"Input: {input_key}")
    print(f"Resolutions: {resolutions}")
    
    # STATUS UPDATE: optimizing
    update_session_status(session_id, 'optimizing', {
        'optimizing_started_at': datetime.utcnow().isoformat(),
        'target_resolutions': json.dumps(resolutions)
    })
    
    work_dir = tempfile.mkdtemp()
    
    try:
        input_filename = os.path.basename(input_key)
        input_path = os.path.join(work_dir, input_filename)
        download_from_s3(input_key, input_path)
        
        input_info = get_video_info(input_path)
        if not input_info:
            raise Exception('Could not read input video')
        
        print(f"Input video: {input_info['width']}x{input_info['height']}, {input_info['duration']:.2f}s")
        
        outputs = []
        
        for idx, resolution in enumerate(resolutions):
            if resolution not in PRESETS:
                print(f"Warning: Unknown resolution {resolution}, skipping")
                continue
            
            # STATUS UPDATE: encoding resolution
            update_session_status(session_id, 'optimizing', {
                'processing_step': f'Encoding {resolution} ({idx + 1}/{len(resolutions)})'
            })
            
            output_filename = f"demo_{session_id}_{resolution}.mp4"
            output_path = os.path.join(work_dir, output_filename)
            
            print(f"\nEncoding {resolution}...")
            optimize_video(input_path, output_path, resolution)
            
            output_info = get_video_info(output_path)
            
            s3_key = f"final/{session_id}/{output_filename}"
            upload_to_s3(output_path, s3_key)
            
            presigned_url = generate_presigned_url(s3_key)
            
            outputs.append({
                'resolution': resolution,
                's3_key': s3_key,
                's3_url': f"s3://{BUCKET_NAME}/{s3_key}",
                'download_url': presigned_url,
                'width': PRESETS[resolution]['width'],
                'height': PRESETS[resolution]['height'],
                'duration': str(output_info['duration']) if output_info else str(input_info['duration']),
                'file_size': output_info['file_size'] if output_info else 0
            })
            
            print(f"✓ {resolution} complete: {s3_key}")
        
        # Generate thumbnail
        thumbnail_info = None
        if generate_thumb:
            # STATUS UPDATE: generating thumbnail
            update_session_status(session_id, 'optimizing', {
                'processing_step': 'Generating thumbnail'
            })
            
            thumbnail_path = os.path.join(work_dir, f"thumbnail_{session_id}.jpg")
            if generate_thumbnail(input_path, thumbnail_path):
                thumb_s3_key = f"final/{session_id}/thumbnail.jpg"
                upload_to_s3(thumbnail_path, thumb_s3_key, 'image/jpeg')
                thumbnail_info = {
                    's3_key': thumb_s3_key,
                    's3_url': f"s3://{BUCKET_NAME}/{thumb_s3_key}",
                    'download_url': generate_presigned_url(thumb_s3_key)
                }
                print(f"✓ Thumbnail generated: {thumb_s3_key}")
        
        # Get the primary download URL (prefer 720p for sharing)
        primary_output = next((o for o in outputs if o['resolution'] == '720p'), outputs[0] if outputs else None)
        
        result = {
            'session_id': session_id,
            'input_key': input_key,
            'input_duration': str(input_info['duration']),
            'input_resolution': f"{input_info['width']}x{input_info['height']}",
            'outputs': outputs,
            'thumbnail': thumbnail_info,
            'resolutions_generated': len(outputs),
            'completed_at': datetime.utcnow().isoformat()
        }
        
        # STATUS UPDATE: completed
        update_session_status(session_id, 'completed', {
            'demo_url': primary_output['download_url'] if primary_output else None,
            'thumbnail_url': thumbnail_info['download_url'] if thumbnail_info else None,
            'final_video_key': primary_output['s3_key'] if primary_output else None,
            'final_video_duration': primary_output['duration'] if primary_output else None,
            'completed_at': datetime.utcnow().isoformat()
        })
        
        return result
        
    except Exception as e:
        # STATUS UPDATE: failed
        update_session_status(session_id, 'optimization_failed', {
            'error_message': str(e),
            'failed_at': datetime.utcnow().isoformat()
        })
        raise
        
    finally:
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)


def lambda_handler(event, context):
    """Lambda handler"""
    print(f"Video Optimizer invoked: {json.dumps(event, indent=2)}")
    
    try:
        result = process_request(event)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'data': result
            })
        }
        
    except ValueError as e:
        print(f"Validation error: {e}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }