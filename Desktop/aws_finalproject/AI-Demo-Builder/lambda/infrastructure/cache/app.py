"""
Cache Service Lambda Function
Manages caching of analysis results in DynamoDB
"""

import json
import os
import boto3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Initialize AWS clients
dynamodb_client = boto3.client('dynamodb')

# Environment variables
CACHE_TABLE = os.environ.get('CACHE_TABLE_NAME', 'ai-demo-builder-cache')
DEFAULT_TTL = int(os.environ.get('CACHE_TTL_SECONDS', '86400'))  # 24 hours


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for Cache Service
    
    Expected event:
    {
        "action": "get" | "set" | "delete",
        "cache_key": "..." (optional, auto-generated if not provided),
        "github_url": "..." (required for set/get),
        "data": {...} (required for set),
        "ttl": 86400 (optional, default 24 hours)
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "status": "success",
            "cached": true/false,
            "data": {...} (for get action),
            "cache_key": "..."
        }
    }
    """
    try:
        action = event.get('action', 'get')
        
        if action == 'get':
            return handle_get_cache(event)
        elif action == 'set':
            return handle_set_cache(event)
        elif action == 'delete':
            return handle_delete_cache(event)
        else:
            return error_response(400, f"Invalid action: {action}")
            
    except Exception as e:
        print(f"Error in Cache Service: {str(e)}")
        return error_response(500, f"Internal error: {str(e)}")


def handle_get_cache(event: Dict[str, Any]) -> Dict[str, Any]:
    """Get cached data"""
    github_url = event.get('github_url')
    branch = event.get('branch', 'main')
    cache_key = event.get('cache_key')
    
    if not cache_key and not github_url:
        return error_response(400, "Missing required field: cache_key or github_url")
    
    if not cache_key:
        cache_key = generate_cache_key(github_url, branch)
    
    try:
        response = dynamodb_client.get_item(
            TableName=CACHE_TABLE,
            Key={'cache_key': {'S': cache_key}}
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'status': 'success',
                    'cached': False,
                    'cache_key': cache_key
                })
            }
        
        item = response['Item']
        expires_at = int(item.get('expires_at', {}).get('N', '0'))
        current_time = int(datetime.now().timestamp())
        
        # Check if expired
        if current_time > expires_at:
            # Delete expired cache
            handle_delete_cache({'cache_key': cache_key})
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'status': 'success',
                    'cached': False,
                    'cache_key': cache_key,
                    'message': 'Cache expired'
                })
            }
        
        # Return cached data
        cached_data = json.loads(item.get('cached_data', {}).get('S', '{}'))
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'cached': True,
                'cache_key': cache_key,
                'data': cached_data,
                'created_at': item.get('created_at', {}).get('N'),
                'expires_at': str(expires_at)
            })
        }
        
    except Exception as e:
        print(f"Error getting cache: {str(e)}")
        return error_response(500, f"Failed to get cache: {str(e)}")


def handle_set_cache(event: Dict[str, Any]) -> Dict[str, Any]:
    """Set cached data"""
    github_url = event.get('github_url')
    branch = event.get('branch', 'main')
    data = event.get('data')
    ttl = event.get('ttl', DEFAULT_TTL)
    cache_key = event.get('cache_key')
    
    if not data:
        return error_response(400, "Missing required field: data")
    
    if not cache_key and not github_url:
        return error_response(400, "Missing required field: cache_key or github_url")
    
    if not cache_key:
        cache_key = generate_cache_key(github_url, branch)
    
    try:
        current_time = int(datetime.now().timestamp())
        expires_at = current_time + ttl
        
        dynamodb_client.put_item(
            TableName=CACHE_TABLE,
            Item={
                'cache_key': {'S': cache_key},
                'repository_url': {'S': github_url or ''},
                'branch': {'S': branch},
                'cached_data': {'S': json.dumps(data)},
                'created_at': {'N': str(current_time)},
                'expires_at': {'N': str(expires_at)}
            }
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'cache_key': cache_key,
                'expires_at': str(expires_at),
                'ttl': ttl
            })
        }
        
    except Exception as e:
        print(f"Error setting cache: {str(e)}")
        return error_response(500, f"Failed to set cache: {str(e)}")


def handle_delete_cache(event: Dict[str, Any]) -> Dict[str, Any]:
    """Delete cached data"""
    cache_key = event.get('cache_key')
    github_url = event.get('github_url')
    branch = event.get('branch', 'main')
    
    if not cache_key and not github_url:
        return error_response(400, "Missing required field: cache_key or github_url")
    
    if not cache_key:
        cache_key = generate_cache_key(github_url, branch)
    
    try:
        dynamodb_client.delete_item(
            TableName=CACHE_TABLE,
            Key={'cache_key': {'S': cache_key}}
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'message': 'Cache deleted',
                'cache_key': cache_key
            })
        }
        
    except Exception as e:
        print(f"Error deleting cache: {str(e)}")
        return error_response(500, f"Failed to delete cache: {str(e)}")


def generate_cache_key(github_url: str, branch: str = 'main') -> str:
    """Generate cache key from GitHub URL and branch"""
    key_input = f"{github_url}:{branch}"
    return hashlib.sha256(key_input.encode()).hexdigest()


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Return standardized error response"""
    return {
        'statusCode': status_code,
        'body': json.dumps({
            'status': 'error',
            'message': message
        })
    }


