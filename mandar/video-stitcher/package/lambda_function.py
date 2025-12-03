"""
Video Stitcher Service
Concatenates videos and slides into a single demo video using FFmpeg.
Uses the FFmpeg Lambda Layer from sampada/ffmpeg-layer/
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

# Video settings
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 30
SLIDE_DURATION = 3  # seconds each slide displays
VIDEO_BITRATE = '5M'
AUDIO_BITRATE = '192k'


def get_video_info(video_path):
    """Get video duration and properties using ffprobe"""
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
        
        duration = float(info.get('format', {}).get('duration', 0))
        
        # Get video stream info
        video_stream = None
        audio_stream = None
        for stream in info.get('streams', []):
            if stream['codec_type'] == 'video' and not video_stream:
                video_stream = stream
            elif stream['codec_type'] == 'audio' and not audio_stream:
                audio_stream = stream
        
        return {
            'duration': duration,
            'width': video_stream.get('width', VIDEO_WIDTH) if video_stream else VIDEO_WIDTH,
            'height': video_stream.get('height', VIDEO_HEIGHT) if video_stream else VIDEO_HEIGHT,
            'has_audio': audio_stream is not None
        }
    except Exception as e:
        print(f"Error getting video info: {e}")
        return {'duration': 0, 'width': VIDEO_WIDTH, 'height': VIDEO_HEIGHT, 'has_audio': False}


def download_from_s3(s3_key, local_path):
    """Download file from S3"""
    print(f"Downloading s3://{BUCKET_NAME}/{s3_key} to {local_path}")
    s3_client.download_file(BUCKET_NAME, s3_key, local_path)
    return local_path


def upload_to_s3(local_path, s3_key):
    """Upload file to S3"""
    print(f"Uploading {local_path} to s3://{BUCKET_NAME}/{s3_key}")
    s3_client.upload_file(
        local_path, 
        BUCKET_NAME, 
        s3_key,
        ExtraArgs={'ContentType': 'video/mp4'}
    )
    return f"s3://{BUCKET_NAME}/{s3_key}"


def create_video_from_slide(slide_path, output_path, duration=SLIDE_DURATION):
    """Convert a slide image to a video clip with specified duration"""
    cmd = [
        FFMPEG_PATH,
        '-y',  # Overwrite output
        '-loop', '1',
        '-i', slide_path,
        '-c:v', 'libx264',
        '-t', str(duration),
        '-pix_fmt', 'yuv420p',
        '-vf', f'scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black',
        '-r', str(VIDEO_FPS),
        '-preset', 'fast',
        output_path
    ]
    
    print(f"Creating video from slide: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    if result.returncode != 0:
        print(f"FFmpeg stderr: {result.stderr}")
        raise Exception(f"Failed to create video from slide: {result.stderr}")
    
    return output_path


def normalize_video(input_path, output_path):
    """Normalize video to standard format for concatenation"""
    cmd = [
        FFMPEG_PATH,
        '-y',
        '-i', input_path,
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-vf', f'scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black,fps={VIDEO_FPS}',
        '-c:a', 'aac',
        '-b:a', AUDIO_BITRATE,
        '-ar', '44100',
        '-ac', '2',
        '-pix_fmt', 'yuv420p',
        output_path
    ]
    
    print(f"Normalizing video: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    
    if result.returncode != 0:
        print(f"FFmpeg stderr: {result.stderr}")
        raise Exception(f"Failed to normalize video: {result.stderr}")
    
    return output_path


def add_silent_audio(input_path, output_path):
    """Add silent audio track to video that doesn't have audio"""
    cmd = [
        FFMPEG_PATH,
        '-y',
        '-i', input_path,
        '-f', 'lavfi',
        '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-shortest',
        output_path
    ]
    
    print(f"Adding silent audio: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    
    if result.returncode != 0:
        print(f"FFmpeg stderr: {result.stderr}")
        raise Exception(f"Failed to add silent audio: {result.stderr}")
    
    return output_path


def concatenate_videos(video_paths, output_path):
    """Concatenate multiple videos using FFmpeg concat demuxer"""
    # Create concat file
    concat_file = output_path.replace('.mp4', '_concat.txt')
    
    with open(concat_file, 'w') as f:
        for video_path in video_paths:
            # Escape single quotes in path
            escaped_path = video_path.replace("'", "'\\''")
            f.write(f"file '{escaped_path}'\n")
    
    print(f"Concat file contents:")
    with open(concat_file, 'r') as f:
        print(f.read())
    
    cmd = [
        FFMPEG_PATH,
        '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_file,
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', AUDIO_BITRATE,
        '-movflags', '+faststart',
        output_path
    ]
    
    print(f"Concatenating videos: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    
    # Cleanup concat file
    if os.path.exists(concat_file):
        os.remove(concat_file)
    
    if result.returncode != 0:
        print(f"FFmpeg stderr: {result.stderr}")
        raise Exception(f"Failed to concatenate videos: {result.stderr}")
    
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
        update_expr += ', stitcher_result = :data'
        expr_values[':data'] = data
    
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
    
    # Get media items (videos and slides)
    # Expected format: list of {type: 'video'|'slide', key: 's3_key', order: int}
    media_items = body.get('media_items', [])
    
    # Alternatively accept separate videos and slides lists
    if not media_items:
        videos = body.get('videos', [])
        slides = body.get('slides', [])
        
        for i, v in enumerate(videos):
            if isinstance(v, str):
                media_items.append({'type': 'video', 'key': v, 'order': (i + 1) * 10})
            else:
                media_items.append({'type': 'video', 'key': v.get('key'), 'order': v.get('order', (i + 1) * 10)})
        
        for i, s in enumerate(slides):
            if isinstance(s, str):
                media_items.append({'type': 'slide', 'key': s, 'order': i * 10 + 5})
            else:
                media_items.append({'type': 'slide', 'key': s.get('key'), 'order': s.get('order', i * 10 + 5)})
    
    if not media_items:
        raise ValueError('media_items, videos, or slides are required')
    
    # Sort by order
    media_items.sort(key=lambda x: x.get('order', 0))
    
    print(f"Processing {len(media_items)} media items for session {session_id}")
    
    # Create temp directory
    work_dir = tempfile.mkdtemp()
    
    try:
        update_session_status(session_id, 'stitching')
        
        normalized_videos = []
        
        for idx, item in enumerate(media_items):
            item_type = item.get('type', 'video')
            s3_key = item.get('key')
            
            if not s3_key:
                continue
            
            # Download from S3
            ext = '.png' if item_type == 'slide' else '.mp4'
            local_path = os.path.join(work_dir, f'input_{idx}{ext}')
            download_from_s3(s3_key, local_path)
            
            normalized_path = os.path.join(work_dir, f'normalized_{idx}.mp4')
            
            if item_type == 'slide':
                # Convert slide to video
                slide_duration = item.get('duration', SLIDE_DURATION)
                slide_video = os.path.join(work_dir, f'slide_video_{idx}.mp4')
                create_video_from_slide(local_path, slide_video, slide_duration)
                
                # Add silent audio
                add_silent_audio(slide_video, normalized_path)
            else:
                # Normalize video
                normalize_video(local_path, normalized_path)
                
                # Check if video has audio, add silent if not
                info = get_video_info(normalized_path)
                if not info.get('has_audio'):
                    temp_with_audio = os.path.join(work_dir, f'with_audio_{idx}.mp4')
                    add_silent_audio(normalized_path, temp_with_audio)
                    shutil.move(temp_with_audio, normalized_path)
            
            normalized_videos.append(normalized_path)
            print(f"Processed item {idx + 1}/{len(media_items)}: {item_type}")
        
        if not normalized_videos:
            raise ValueError('No valid media items to stitch')
        
        # Concatenate all videos
        output_filename = f"stitched_{session_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.mp4"
        output_path = os.path.join(work_dir, output_filename)
        
        concatenate_videos(normalized_videos, output_path)
        
        # Get output video info
        output_info = get_video_info(output_path)
        
        # Upload to S3
        output_s3_key = f"output/{session_id}/{output_filename}"
        upload_to_s3(output_path, output_s3_key)
        
        result = {
            'session_id': session_id,
            'output_key': output_s3_key,
            'output_url': f"s3://{BUCKET_NAME}/{output_s3_key}",
            'duration': str(output_info['duration']),
            'resolution': f"{output_info['width']}x{output_info['height']}",
            'items_processed': len(normalized_videos),
            'created_at': datetime.utcnow().isoformat()
        }
        
        update_session_status(session_id, 'stitched', result)
        
        return result
        
    finally:
        # Cleanup temp directory
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)


def lambda_handler(event, context):
    """Lambda handler"""
    print(f"Video Stitcher invoked: {json.dumps(event, indent=2)}")
    
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
            if 'session_id' in str(event):
                body = event.get('body', event)
                if isinstance(body, str):
                    body = json.loads(body)
                session_id = body.get('session_id')
                if session_id:
                    update_session_status(session_id, 'failed', {'error': str(e)})
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