"""
Video Optimizer Service
Encodes video in multiple resolutions (1080p, 720p) with optimized settings.
Generates web-optimized MP4 files with fast-start for streaming.
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
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'ai-demo-builder-bucket')
TABLE_NAME = os.environ.get('TABLE_NAME', 'Sessions')
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
    
    # Build FFmpeg command
    cmd = [
        FFMPEG_PATH,
        '-y',
        '-i', input_path,
        # Video settings
        '-c:v', 'libx264',
        '-preset', 'medium',  # Balance between speed and quality
        '-crf', str(preset['crf']),
        '-maxrate', preset['maxrate'],
        '-bufsize', preset['bufsize'],
        '-vf', f"scale={preset['width']}:{preset['height']}:force_original_aspect_ratio=decrease,pad={preset['width']}:{preset['height']}:(ow-iw)/2:(oh-ih)/2:black",
        '-pix_fmt', 'yuv420p',
        # Audio settings
        '-c:a', 'aac',
        '-b:a', preset['audio_bitrate'],
        '-ar', '44100',
        '-ac', '2',
        # MP4 optimization for web streaming
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


def update_session_status(session_id, status, data=None):
    """Update session status in DynamoDB"""
    table = dynamodb.Table(TABLE_NAME)
    
    update_expr = 'SET #status = :status, updated_at = :now'
    expr_values = {
        ':status': status,
        ':now': datetime.utcnow().isoformat()
    }
    expr_names = {'#status': 'status'}
    
    if data:
        update_expr += ', optimizer_result = :data, final_outputs = :outputs'
        expr_values[':data'] = data
        expr_values[':outputs'] = data.get('outputs', [])
    
    table.update_item(
        Key={'session_id': session_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values
    )


def process_request(event):
    """Main processing logic"""
    # Parse input
    if isinstance(event.get('body'), str):
        body = json.loads(event['body'])
    elif event.get('body'):
        body = event['body']
    else:
        body = event
    
    session_id = body.get('session_id')
    if not session_id:
        raise ValueError('session_id is required')
    
    # Input video key (from video stitcher output)
    input_key = body.get('input_key')
    if not input_key:
        raise ValueError('input_key is required')
    
    # Resolutions to generate (default: 1080p and 720p)
    resolutions = body.get('resolutions', ['1080p', '720p'])
    
    # Whether to generate thumbnail
    generate_thumb = body.get('generate_thumbnail', True)
    
    print(f"Optimizing video for session {session_id}")
    print(f"Input: {input_key}")
    print(f"Resolutions: {resolutions}")
    
    # Create temp directory
    work_dir = tempfile.mkdtemp()
    
    try:
        update_session_status(session_id, 'optimizing')
        
        # Download input video
        input_filename = os.path.basename(input_key)
        input_path = os.path.join(work_dir, input_filename)
        download_from_s3(input_key, input_path)
        
        # Get input video info
        input_info = get_video_info(input_path)
        if not input_info:
            raise Exception('Could not read input video')
        
        print(f"Input video: {input_info['width']}x{input_info['height']}, {input_info['duration']:.2f}s")
        
        outputs = []
        
        # Generate each resolution
        for resolution in resolutions:
            if resolution not in PRESETS:
                print(f"Warning: Unknown resolution {resolution}, skipping")
                continue
            
            output_filename = f"demo_{session_id}_{resolution}.mp4"
            output_path = os.path.join(work_dir, output_filename)
            
            print(f"\nEncoding {resolution}...")
            optimize_video(input_path, output_path, resolution)
            
            # Get output info
            output_info = get_video_info(output_path)
            
            # Upload to S3
            s3_key = f"final/{session_id}/{output_filename}"
            upload_to_s3(output_path, s3_key)
            
            # Generate presigned URL
            presigned_url = generate_presigned_url(s3_key)
            
            outputs.append({
                'resolution': resolution,
                's3_key': s3_key,
                's3_url': f"s3://{BUCKET_NAME}/{s3_key}",
                'download_url': presigned_url,
                'width': PRESETS[resolution]['width'],
                'height': PRESETS[resolution]['height'],
                'duration': output_info['duration'] if output_info else input_info['duration'],
                'file_size': output_info['file_size'] if output_info else 0
            })
            
            print(f"✓ {resolution} complete: {s3_key}")
        
        # Generate thumbnail
        thumbnail_info = None
        if generate_thumb:
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
        
        result = {
            'session_id': session_id,
            'input_key': input_key,
            'input_duration': input_info['duration'],
            'input_resolution': f"{input_info['width']}x{input_info['height']}",
            'outputs': outputs,
            'thumbnail': thumbnail_info,
            'resolutions_generated': len(outputs),
            'completed_at': datetime.utcnow().isoformat()
        }
        
        update_session_status(session_id, 'completed', result)
        
        return result
        
    finally:
        # Cleanup temp directory
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
        
        # Try to update session status
        try:
            body = event.get('body', event)
            if isinstance(body, str):
                body = json.loads(body)
            session_id = body.get('session_id')
            if session_id:
                update_session_status(session_id, 'optimization_failed', {'error': str(e)})
        except:
            pass
        
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