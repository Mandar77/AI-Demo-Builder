"""
Error handling utilities for Lambda functions
"""
import json
import traceback


def create_response(status_code, body, headers=None):
    """
    Create a standardized API Gateway response
    
    Args:
        status_code: HTTP status code
        body: Response body (dict or string)
        headers: Optional custom headers
    
    Returns:
        dict: API Gateway response format
    """
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }
    
    if headers:
        default_headers.update(headers)
    
    if isinstance(body, dict):
        body = json.dumps(body)
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': body
    }


def success_response(data, status_code=200):
    """
    Create a success response
    
    Args:
        data: Response data
        status_code: HTTP status code (default 200)
    
    Returns:
        dict: API Gateway response
    """
    return create_response(status_code, data)


def error_response(message, status_code=500, error_type='InternalServerError'):
    """
    Create an error response
    
    Args:
        message: Error message
        status_code: HTTP status code (default 500)
        error_type: Error type
    
    Returns:
        dict: API Gateway response
    """
    error_body = {
        'error': error_type,
        'message': message
    }
    return create_response(status_code, error_body)


def handle_lambda_error(func):
    """
    Decorator to handle errors in Lambda functions
    
    Args:
        func: Lambda handler function
    
    Returns:
        Wrapped function with error handling
    """
    def wrapper(event, context):
        try:
            return func(event, context)
        except ValueError as e:
            print(f"Validation error: {e}")
            return error_response(str(e), 400, 'ValidationError')
        except KeyError as e:
            print(f"Missing key: {e}")
            return error_response(f"Missing required field: {e}", 400, 'MissingFieldError')
        except Exception as e:
            print(f"Unexpected error: {e}")
            print(traceback.format_exc())
            return error_response(str(e), 500, 'InternalServerError')
    
    return wrapper

