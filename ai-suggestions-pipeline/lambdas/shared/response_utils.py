import json
from typing import Dict, Any, Optional

def success_response(data: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
    """
    Create a successful API Gateway response
    
    Args:
        data: Response data to return
        status_code: HTTP status code (default: 200)
    
    Returns:
        Formatted API Gateway response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps(data)
    }


def error_response(message: str, status_code: int = 500, error_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Create an error API Gateway response
    
    Args:
        message: Error message
        status_code: HTTP status code (default: 500)
        error_type: Type of error (optional)
    
    Returns:
        Formatted API Gateway error response
    """
    error_data = {
        'error': message
    }
    
    if error_type:
        error_data['error_type'] = error_type
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps(error_data)
    }