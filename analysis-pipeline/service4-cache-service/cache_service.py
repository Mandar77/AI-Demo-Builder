"""
Service 4: Cache Service
Manages DynamoDB cache for storing and retrieving cached data
"""

import json
import os
from typing import Dict, Any, Optional

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    # For local testing without boto3
    boto3 = None
    ClientError = Exception


def get_dynamodb_table():
    """
    Get DynamoDB table instance
    
    Returns:
        DynamoDB Table resource
    """
    if boto3 is None:
        raise ImportError("boto3 is required for DynamoDB operations")
    
    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ.get('DYNAMODB_TABLE', 'ai-demo-cache')
    
    print(f"[Service4] Connecting to DynamoDB table: {table_name}")
    return dynamodb.Table(table_name)


def get_cache_item(key: str) -> Optional[Dict[str, Any]]:
    """
    Get item from cache
    
    Args:
        key: Cache key
        
    Returns:
        Cached value if found, None otherwise
    """
    try:
        table = get_dynamodb_table()
        response = table.get_item(
            Key={
                'cacheKey': key
            }
        )
        
        if 'Item' in response:
            item = response['Item']
            # Extract the value (assuming it's stored in 'value' field)
            cached_value = item.get('value')
            print(f"[Service4] ✅ Cache hit for key: {key}")
            return cached_value
        else:
            print(f"[Service4] Cache miss for key: {key}")
            return None
            
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ResourceNotFoundException':
            raise Exception(f"DynamoDB table not found. Please create table: {os.environ.get('DYNAMODB_TABLE', 'ai-demo-cache')}")
        raise Exception(f"DynamoDB error: {str(e)}")


def set_cache_item(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """
    Store item in cache
    
    Args:
        key: Cache key
        value: Value to cache
        ttl: Optional TTL in seconds (for DynamoDB TTL feature)
        
    Returns:
        True if successful
    """
    try:
        table = get_dynamodb_table()
        
        item = {
            'cacheKey': key,
            'value': value
        }
        
        # Add TTL if provided (DynamoDB requires timestamp, not seconds from now)
        if ttl:
            import time
            item['ttl'] = int(time.time()) + ttl
        
        table.put_item(Item=item)
        print(f"[Service4] ✅ Cached item for key: {key}")
        return True
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ResourceNotFoundException':
            raise Exception(f"DynamoDB table not found. Please create table: {os.environ.get('DYNAMODB_TABLE', 'ai-demo-cache')}")
        raise Exception(f"DynamoDB error: {str(e)}")


def delete_cache_item(key: str) -> bool:
    """
    Delete item from cache
    
    Args:
        key: Cache key to delete
        
    Returns:
        True if successful
    """
    try:
        table = get_dynamodb_table()
        table.delete_item(
            Key={
                'cacheKey': key
            }
        )
        print(f"[Service4] ✅ Deleted cache item: {key}")
        return True
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ResourceNotFoundException':
            raise Exception(f"DynamoDB table not found. Please create table: {os.environ.get('DYNAMODB_TABLE', 'ai-demo-cache')}")
        raise Exception(f"DynamoDB error: {str(e)}")


def process_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process the Lambda event and perform cache operation
    
    Args:
        event: Lambda event containing operation, key, and optionally value
        
    Returns:
        Cache operation result
    """
    operation = event.get('operation', '').lower()
    key = event.get('key')
    
    if not operation:
        raise ValueError("Missing required field: operation")
    
    if not key:
        raise ValueError("Missing required field: key")
    
    # Handle different operations
    if operation == 'get':
        cached_value = get_cache_item(key)
        return {
            "found": cached_value is not None,
            "value": cached_value
        }
    
    elif operation == 'set':
        value = event.get('value')
        if value is None:
            raise ValueError("Missing required field: value for set operation")
        
        # Optional TTL (in seconds)
        ttl = event.get('ttl')
        set_cache_item(key, value, ttl)
        return {
            "success": True,
            "key": key
        }
    
    elif operation == 'delete':
        delete_cache_item(key)
        return {
            "success": True,
            "key": key
        }
    
    else:
        raise ValueError(f"Unsupported operation: {operation}. Supported operations: get, set, delete")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function
    
    Standard Lambda entry point for Service 4: Cache Service
    
    Args:
        event: Input data containing operation, key, and optionally value
        context: Lambda runtime context
        
    Returns:
        Standard Lambda response with statusCode and body
    """
    try:
        print(f"[Service4] Starting cache service")
        result = process_request(event)
        
        return {
            "statusCode": 200,
            "body": result
        }
        
    except ValueError as e:
        print(f"[Service4] ❌ Validation Error: {str(e)}")
        return {
            "statusCode": 400,
            "body": {"error": str(e)}
        }
        
    except ImportError as e:
        print(f"[Service4] ❌ Import Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": {"error": "boto3 library not available. This service requires boto3 for AWS Lambda."}
        }
        
    except Exception as e:
        print(f"[Service4] ❌ Error: {str(e)}")
        error_message = str(e)
        
        # Check for DynamoDB table not found
        if "table not found" in error_message.lower():
            status_code = 503  # Service unavailable
        else:
            status_code = 500
        
        return {
            "statusCode": status_code,
            "body": {"error": error_message}
        }

