import json
import boto3
import subprocess
import os

s3 = boto3.client('s3')
BUCKET = 'cs6620-ai-demo-builder'

def lambda_handler(event, context):
    try:
        if 'Records' in event:
            key = event['Records'][0]['s3']['object']['key']
        else:
            body = json.loads(event.get('body', '{}'))
            key = body.get('video_key')
        
        if not key:
            return error_response('No video key provided')
        
        print(f'Converting video: {key}')
        
        parts = key.split('/')
        session_id = parts[1]
        video_num = parts[2].replace('.mp4', '')
        
        local_input = '/tmp/input.mp4'
        s3.download_file(BUCKET, key, local_input)
        
        local_output = '/tmp/output.mp4'
        convert_video(local_input, local_output)
        
        converted_key = f'videos/{session_id}/{video_num}_converted.mp4'
        s3.upload_file(local_output, BUCKET, converted_key)
        
        print(f'✅ Video converted: {converted_key}')
        
        os.remove(local_input)
        os.remove(local_output)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Converted successfully',
                'converted_key': converted_key
            })
        }
        
    except Exception as e:
        print(f'Error: {str(e)}')
        return error_response(str(e))

def convert_video(input_path, output_path):
    """Convert with FFmpeg"""
    cmd = [
        '/opt/bin/ffmpeg',
        '-i', input_path,
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-movflags', '+faststart',
        '-y',
        output_path
    ]
    
    print('Running FFmpeg conversion...')
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f'FFmpeg error: {result.stderr}')
    
    print('FFmpeg conversion complete')

def error_response(message):
    return {
        'statusCode': 500,
        'body': json.dumps({'error': message})
    }
