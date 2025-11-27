import json
import boto3
import os

s3 = boto3.client('s3')
BUCKET = 'cs6620-ai-demo-builder'
MAX_SIZE_MB = 100

def lambda_handler(event, context):
    try:
        if 'Records' in event:
            key = event['Records'][0]['s3']['object']['key']
        else:
            body = json.loads(event.get('body', '{}'))
            key = body.get('video_key')
        
        if not key:
            return error_response('No video key provided')
        
        print(f'Validating video: {key}')
        
        # Get file metadata (no download needed)
        response = s3.head_object(Bucket=BUCKET, Key=key)
        size_bytes = response['ContentLength']
        size_mb = size_bytes / (1024 * 1024)
        
        print(f'Video size: {size_mb:.2f} MB')
        
        if size_mb > MAX_SIZE_MB:
            return validation_failed(f'Video too large: {size_mb:.1f} MB (max {MAX_SIZE_MB} MB)')
        
        # Check content type
        content_type = response.get('ContentType', '')
        if 'video' not in content_type.lower():
            return validation_failed(f'Not a video file: {content_type}')
        
        print('✅ Video is valid')
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'valid': True,
                'size_mb': round(size_mb, 2),
                'content_type': content_type
            })
        }
        
    except Exception as e:
        print(f'Error: {str(e)}')
        return error_response(str(e))

def validation_failed(message):
    return {
        'statusCode': 400,
        'body': json.dumps({'valid': False, 'error': message})
    }

def error_response(message):
    return {
        'statusCode': 500,
        'body': json.dumps({'valid': False, 'error': message})
    }
