"""
S3 utility functions for Lambda functions
"""
import boto3
import os
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')
BUCKET_NAME = os.environ.get('S3_BUCKET', 'cs6620-ai-demo-builder')


def upload_file(file_path, s3_key, content_type=None):
    """
    Upload a file to S3
    
    Args:
        file_path: Local file path
        s3_key: S3 object key
        content_type: Optional content type
    
    Returns:
        str: S3 URL of uploaded file
    """
    try:
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        
        s3_client.upload_file(file_path, BUCKET_NAME, s3_key, ExtraArgs=extra_args)
        return f"s3://{BUCKET_NAME}/{s3_key}"
    except ClientError as e:
        print(f"Error uploading to S3: {e}")
        raise


def download_file(s3_key, local_path):
    """
    Download a file from S3
    
    Args:
        s3_key: S3 object key
        local_path: Local file path to save to
    """
    try:
        s3_client.download_file(BUCKET_NAME, s3_key, local_path)
    except ClientError as e:
        print(f"Error downloading from S3: {e}")
        raise


def get_presigned_url(s3_key, expiration=3600, method='get_object'):
    """
    Generate a presigned URL for S3 object
    
    Args:
        s3_key: S3 object key
        expiration: URL expiration time in seconds
        method: S3 operation (get_object, put_object)
    
    Returns:
        str: Presigned URL
    """
    try:
        if method == 'get_object':
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
                ExpiresIn=expiration
            )
        elif method == 'put_object':
            url = s3_client.generate_presigned_url(
                'put_object',
                Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
                ExpiresIn=expiration
            )
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return url
    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        raise


def delete_file(s3_key):
    """
    Delete a file from S3
    
    Args:
        s3_key: S3 object key
    """
    try:
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=s3_key)
    except ClientError as e:
        print(f"Error deleting from S3: {e}")
        raise


def list_files(prefix):
    """
    List files in S3 with given prefix
    
    Args:
        prefix: S3 key prefix
    
    Returns:
        list: List of S3 object keys
    """
    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
        if 'Contents' in response:
            return [obj['Key'] for obj in response['Contents']]
        return []
    except ClientError as e:
        print(f"Error listing S3 objects: {e}")
        return []

