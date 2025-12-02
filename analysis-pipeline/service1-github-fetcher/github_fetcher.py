"""
Service 1: GitHub Repository Fetcher
Fetches GitHub repository information and README content
"""

import json
import os
import re
import requests
from typing import Dict, Any, Optional

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    # boto3 may not be available in local testing
    boto3 = None
    ClientError = Exception


def extract_owner_repo(github_url: str) -> Optional[Dict[str, str]]:
    """
    Extract owner and repo name from GitHub URL
    
    Args:
        github_url: GitHub repository URL
        
    Returns:
        Dict with 'owner' and 'repo' keys, or None if invalid
    """
    # Handle various GitHub URL formats
    patterns = [
        r'github\.com/([^/]+)/([^/?#]+)',
        r'github\.com/([^/]+)/([^/?#]+)\.git',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, github_url)
        if match:
            return {
                'owner': match.group(1),
                'repo': match.group(2).replace('.git', '')
            }
    
    return None


def fetch_repository_info(owner: str, repo: str, token: str = None) -> Dict[str, Any]:
    """
    Fetch repository information from GitHub API
    
    Args:
        owner: Repository owner
        repo: Repository name
        token: GitHub personal access token (optional)
        
    Returns:
        Repository information dict
    """
    github_api = os.environ.get('GITHUB_API', 'https://api.github.com')
    url = f"{github_api}/repos/{owner}/{repo}"
    
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'github-fetcher-service'
    }
    
    if token:
        headers['Authorization'] = f'token {token}'
    
    print(f"[Service1] Fetching repository info: {owner}/{repo}")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 404:
        raise Exception("Repository not found")
    elif response.status_code == 403:
        raise Exception("Rate limit exceeded or access forbidden")
    elif response.status_code == 401:
        raise Exception("Invalid or missing GitHub token")
    elif response.status_code != 200:
        raise Exception(f"GitHub API error: {response.status_code}")
    
    return response.json()


def fetch_readme(owner: str, repo: str, token: str = None) -> str:
    """
    Fetch README content from GitHub repository
    
    Args:
        owner: Repository owner
        repo: Repository name
        token: GitHub personal access token (optional)
        
    Returns:
        README content as string
    """
    github_api = os.environ.get('GITHUB_API', 'https://api.github.com')
    url = f"{github_api}/repos/{owner}/{repo}/readme"
    
    headers = {
        'Accept': 'application/vnd.github.v3.raw',
        'User-Agent': 'github-fetcher-service'
    }
    
    if token:
        headers['Authorization'] = f'token {token}'
    
    print(f"[Service1] Fetching README: {owner}/{repo}")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 404:
        # README not found is not critical, return empty string
        print(f"[Service1] README not found for {owner}/{repo}")
        return ""
    elif response.status_code != 200:
        print(f"[Service1] Warning: Could not fetch README ({response.status_code})")
        return ""
    
    return response.text


def process_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process the Lambda event and fetch GitHub repository data
    
    Args:
        event: Lambda event containing github_url (direct invoke) or body (API Gateway)
        
    Returns:
        Processed repository data
    """
    # Handle API Gateway event format (body is JSON string)
    if 'body' in event and isinstance(event.get('body'), str):
        try:
            body_data = json.loads(event['body'])
            github_url = body_data.get('github_url')
        except (json.JSONDecodeError, TypeError):
            github_url = None
    else:
        # Direct Lambda invoke format
        github_url = event.get('github_url')
    
    if not github_url:
        raise ValueError("Missing required field: github_url")
    
    # Extract owner and repo from URL
    owner_repo = extract_owner_repo(github_url)
    if not owner_repo:
        raise ValueError(f"Invalid GitHub URL format: {github_url}")
    
    owner = owner_repo['owner']
    repo = owner_repo['repo']
    
    # Get GitHub token from environment
    github_token = os.environ.get('GITHUB_TOKEN', '')
    
    # Fetch repository information
    repo_info = fetch_repository_info(owner, repo, github_token if github_token else None)
    
    # Fetch README content
    readme_content = fetch_readme(owner, repo, github_token if github_token else None)
    
    # Build response
    result = {
        "projectName": repo_info.get('name', repo),
        "owner": repo_info.get('owner', {}).get('login', owner),
        "stars": repo_info.get('stargazers_count', 0),
        "language": repo_info.get('language', ''),
        "topics": repo_info.get('topics', []),
        "description": repo_info.get('description', ''),
        "readme": readme_content
    }
    
    print(f"[Service1] ✅ Successfully fetched data for {owner}/{repo}")
    return result


def invoke_lambda_service(function_name: str, payload: Dict[str, Any], region: str = 'us-west-1') -> Dict[str, Any]:
    """
    Invoke another Lambda function
    
    Args:
        function_name: Name of the Lambda function to invoke
        payload: Payload to send to the function
        region: AWS region
        
    Returns:
        Response from the Lambda function
        
    Raises:
        Exception: If invocation fails
    """
    if boto3 is None:
        raise ImportError("boto3 is required for Lambda-to-Lambda invocation")
    
    try:
        lambda_client = boto3.client('lambda', region_name=region)
        print(f"[Service1] Invoking {function_name}...")
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') != 200:
            error_msg = result.get('body', {}).get('error', 'Unknown error')
            raise Exception(f"{function_name} returned error: {error_msg}")
        
        print(f"[Service1] ✅ {function_name} invocation successful")
        return result.get('body', {})
        
    except ClientError as e:
        raise Exception(f"Failed to invoke {function_name}: {str(e)}")


def call_service2_parse_readme(readme: str) -> Dict[str, Any]:
    """
    Call Service 2 to parse README content
    
    Args:
        readme: README content string
        
    Returns:
        Parsed README data from Service 2
    """
    payload = {"readme": readme}
    return invoke_lambda_service('service2-readme-parser', payload)


def call_service3_analyze_project(github_data: Dict[str, Any], parsed_readme: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call Service 3 to analyze project
    
    Args:
        github_data: GitHub repository data (from Service 1)
        parsed_readme: Parsed README data (from Service 2)
        
    Returns:
        Project analysis from Service 3
    """
    # Remove readme from github_data before sending to Service 3
    github_data_for_service3 = {k: v for k, v in github_data.items() if k != 'readme'}
    
    payload = {
        "github_data": github_data_for_service3,
        "parsed_readme": parsed_readme
    }
    return invoke_lambda_service('service3-project-analyzer', payload)


def call_service4_cache_result(key: str, value: Dict[str, Any], ttl: int = 3600) -> bool:
    """
    Call Service 4 to cache result (optional)
    
    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds
        
    Returns:
        True if successful
    """
    try:
        payload = {
            "operation": "set",
            "key": key,
            "value": value,
            "ttl": ttl
        }
        invoke_lambda_service('service4-cache-service', payload)
        return True
    except Exception as e:
        print(f"[Service1] ⚠️  Cache failed (non-critical): {str(e)}")
        return False


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function
    
    Standard Lambda entry point for Service 1: GitHub Fetcher
    Supports both direct Lambda invoke and API Gateway invoke
    
    Args:
        event: Input data containing github_url (direct) or body (API Gateway)
        context: Lambda runtime context
        
    Returns:
        Standard Lambda response with statusCode and body
        For API Gateway (AWS_PROXY): body must be JSON string
        For direct invoke: body can be object
    """
    try:
        print(f"[Service1] Starting GitHub fetch service")
        
        # Step 1: Fetch GitHub data
        github_data = process_request(event)
        
        # Step 2: Call Service 2 to parse README
        print(f"[Service1] Calling Service 2 to parse README...")
        parsed_readme = call_service2_parse_readme(github_data.get('readme', ''))
        
        # Step 3: Call Service 3 to analyze project
        print(f"[Service1] Calling Service 3 to analyze project...")
        project_analysis = call_service3_analyze_project(github_data, parsed_readme)
        
        # Combine all results
        result = {
            "github_data": github_data,
            "parsed_readme": parsed_readme,
            "project_analysis": project_analysis
        }
        
        # Step 4: Cache the complete result in DynamoDB (non-blocking)
        cache_key = f"github_{github_data.get('owner', '')}_{github_data.get('projectName', '')}"
        call_service4_cache_result(cache_key, result)
        
        # Check if this is an API Gateway request (AWS_PROXY integration)
        # API Gateway expects body as JSON string
        is_api_gateway = 'requestContext' in event or ('body' in event and isinstance(event.get('body'), str))
        
        if is_api_gateway:
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps(result)
            }
        else:
            # Direct Lambda invoke - return object
            return {
                "statusCode": 200,
                "body": result
            }
        
    except ValueError as e:
        print(f"[Service1] ❌ Validation Error: {str(e)}")
        error_response = {"error": str(e)}
        is_api_gateway = 'requestContext' in event or ('body' in event and isinstance(event.get('body'), str))
        
        if is_api_gateway:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps(error_response)
            }
        else:
            return {
                "statusCode": 400,
                "body": error_response
            }
        
    except Exception as e:
        print(f"[Service1] ❌ Error: {str(e)}")
        error_message = str(e)
        
        # Map specific errors to status codes
        if "Repository not found" in error_message:
            status_code = 404
        elif "Rate limit" in error_message or "forbidden" in error_message.lower():
            status_code = 403
        elif "Invalid" in error_message or "token" in error_message.lower():
            status_code = 401
        else:
            status_code = 500
        
        error_response = {"error": error_message}
        is_api_gateway = 'requestContext' in event or ('body' in event and isinstance(event.get('body'), str))
        
        if is_api_gateway:
            return {
                "statusCode": status_code,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps(error_response)
            }
        else:
            return {
                "statusCode": status_code,
                "body": error_response
            }

