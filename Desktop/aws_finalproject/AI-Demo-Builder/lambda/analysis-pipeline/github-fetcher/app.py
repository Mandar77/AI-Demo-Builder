"""
GitHub Fetcher Lambda Function
Fetches repository content from GitHub and stores in S3
"""

import json
import os
import boto3
from datetime import datetime
from typing import Dict, Any, List, Optional
import hashlib
import base64

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb_client = boto3.client('dynamodb')

# Environment variables
S3_BUCKET = os.environ.get('S3_BUCKET_NAME', 'ai-demo-builder-repos')
DYNAMODB_TABLE = os.environ.get('JOBS_TABLE_NAME', 'ai-demo-builder-jobs')

# GitHub API token (should be stored in AWS Secrets Manager in production)
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')

# Try to import PyGithub, if not available we'll use GitHub API directly
try:
    from github import Github
    PYGITHUB_AVAILABLE = True
except ImportError:
    PYGITHUB_AVAILABLE = False

# Import requests for fallback GitHub API (should always be available)
import requests
REQUESTS_AVAILABLE = True


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for GitHub Fetcher
    
    Expected event:
    {
        "github_url": "https://github.com/user/repo",
        "job_id": "unique-job-id",
        "branch": "main" (optional)
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "status": "success",
            "job_id": "...",
            "repo_name": "...",
            "s3_location": "s3://bucket/path",
            "files_count": 50,
            "languages": ["Python"],
            "structure": {...}
        }
    }
    """
    try:
        # Extract input
        github_url = event.get('github_url')
        job_id = event.get('job_id', generate_job_id(github_url))
        branch = event.get('branch', 'main')
        
        if not github_url:
            return error_response(400, "Missing required field: github_url")
        
        # Parse GitHub URL to get owner/repo
        repo_name = extract_repo_name(github_url)
        owner, repo = parse_github_url(github_url)
        
        if not owner or not repo:
            return error_response(400, f"Invalid GitHub URL: {github_url}")
        
        # Fetch repository content
        print(f"Fetching repository: {owner}/{repo} (branch: {branch})")
        repo_data = fetch_repository(owner, repo, branch)
        
        if not repo_data:
            return error_response(500, f"Failed to fetch repository: {owner}/{repo}")
        
        # Upload files to S3
        s3_location = f"s3://{S3_BUCKET}/repos/{job_id}/"
        files_count = upload_to_s3(repo_data['files'], job_id, owner, repo)
        
        # Extract metadata
        languages = extract_languages(repo_data['files'])
        structure = build_file_structure(repo_data['files'])
        
        # Update job status in DynamoDB
        metadata = {
            's3_location': s3_location,
            'repo_name': repo_name,
            'owner': owner,
            'repo': repo,
            'branch': branch,
            'files_count': files_count,
            'languages': languages
        }
        update_job_status(job_id, 'fetching_complete', metadata)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'job_id': job_id,
                'repo_name': repo_name,
                'github_url': github_url,
                's3_location': s3_location,
                'files_count': files_count,
                'languages': languages,
                'structure': structure
            })
        }
        
    except Exception as e:
        print(f"Error in GitHub Fetcher: {str(e)}")
        return error_response(500, f"Internal error: {str(e)}")


def parse_github_url(github_url: str) -> tuple:
    """Parse GitHub URL to extract owner and repo name"""
    # Remove protocol and www
    url = github_url.replace('https://', '').replace('http://', '').replace('www.', '')
    
    # Remove github.com
    if url.startswith('github.com/'):
        url = url[11:]
    elif url.startswith('github.com'):
        url = url[10:]
    
    # Split by /
    parts = url.rstrip('/').split('/')
    
    if len(parts) >= 2:
        owner = parts[0]
        repo = parts[1].replace('.git', '')  # Remove .git if present
        return owner, repo
    
    return None, None


def extract_repo_name(github_url: str) -> str:
    """Extract repository name from GitHub URL"""
    owner, repo = parse_github_url(github_url)
    if owner and repo:
        return f"{owner}/{repo}"
    return "unknown/repo"


def generate_job_id(github_url: str) -> str:
    """Generate unique job ID from GitHub URL"""
    timestamp = datetime.now().isoformat()
    hash_input = f"{github_url}{timestamp}"
    return hashlib.sha256(hash_input.encode()).hexdigest()[:16]


def update_job_status(job_id: str, status: str, metadata: Dict[str, Any]):
    """Update job status in DynamoDB"""
    try:
        dynamodb_client.update_item(
            TableName=DYNAMODB_TABLE,
            Key={'jobId': {'S': job_id}},
            UpdateExpression='SET #status = :status, #metadata = :metadata, #updated = :updated',
            ExpressionAttributeNames={
                '#status': 'status',
                '#metadata': 'metadata',
                '#updated': 'updated_at'
            },
            ExpressionAttributeValues={
                ':status': {'S': status},
                ':metadata': {'S': json.dumps(metadata)},
                ':updated': {'N': str(int(datetime.now().timestamp()))}
            }
        )
    except Exception as e:
        print(f"Failed to update job status: {str(e)}")
        # Don't fail the whole function if DynamoDB update fails


def fetch_repository(owner: str, repo: str, branch: str = 'main') -> Optional[Dict[str, Any]]:
    """
    Fetch repository content from GitHub
    
    Returns:
    {
        'files': [
            {'path': 'path/to/file', 'content': 'file content', 'size': 1234},
            ...
        ],
        'tree': {...}
    }
    """
    files = []
    
    if PYGITHUB_AVAILABLE and GITHUB_TOKEN:
        try:
            # Use PyGithub
            g = Github(GITHUB_TOKEN)
            github_repo = g.get_repo(f"{owner}/{repo}")
            contents = github_repo.get_contents("", ref=branch)
            
            # Recursively get all files
            files = get_repo_contents_recursive(github_repo, contents, branch, "")
            return {'files': files}
        except Exception as e:
            print(f"PyGithub error: {str(e)}, falling back to GitHub API")
    
    # Fallback to GitHub REST API (requests should always be available)
    try:
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'ai-demo-builder'
        }
        if GITHUB_TOKEN:
            headers['Authorization'] = f'token {GITHUB_TOKEN}'
        
        # First, get the default branch or verify branch exists
        repo_info_url = f"https://api.github.com/repos/{owner}/{repo}"
        repo_response = requests.get(repo_info_url, headers=headers, timeout=30)
        
        if repo_response.status_code != 200:
            print(f"GitHub API error getting repo info: {repo_response.status_code} - {repo_response.text}")
            return None
        
        repo_info = repo_response.json()
        default_branch = repo_info.get('default_branch', 'main')
        
        # Use the provided branch or default branch
        actual_branch = branch if branch else default_branch
        
        # Get branch SHA (needed for git/trees API)
        branch_url = f"https://api.github.com/repos/{owner}/{repo}/branches/{actual_branch}"
        branch_response = requests.get(branch_url, headers=headers, timeout=30)
        
        if branch_response.status_code != 200:
            print(f"GitHub API error getting branch: {branch_response.status_code} - {branch_response.text}")
            # Fallback: try to use the branch name directly (might work for some repos)
            branch_sha = actual_branch
        else:
            branch_data = branch_response.json()
            branch_sha = branch_data['commit']['sha']
        
        # Get repository tree using SHA
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch_sha}?recursive=1"
        response = requests.get(tree_url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"GitHub API error: {response.status_code} - {response.text}")
            return None
        
        tree_data = response.json()
        
        # Get file contents
        for item in tree_data.get('tree', []):
            if item['type'] == 'blob':  # It's a file
                file_path = item['path']
                file_url = item['url']
                
                # Fetch file content
                file_response = requests.get(file_url, headers=headers, timeout=30)
                if file_response.status_code == 200:
                    file_data = file_response.json()
                    
                    # Decode content if it's base64 encoded
                    content = file_data.get('content', '')
                    if file_data.get('encoding') == 'base64':
                        try:
                            content = base64.b64decode(content).decode('utf-8', errors='ignore')
                        except:
                            content = ''
                    
                    files.append({
                        'path': file_path,
                        'content': content,
                        'size': item.get('size', 0),
                        'sha': item.get('sha', '')
                    })
        
        return {'files': files}
        
    except Exception as e:
        print(f"GitHub API error: {str(e)}")
        return None


def get_repo_contents_recursive(repo, contents, branch: str, base_path: str) -> List[Dict]:
    """Recursively get all file contents from repository using PyGithub"""
    files = []
    
    for content in contents:
        if content.type == 'file':
            try:
                file_content = content.decoded_content.decode('utf-8', errors='ignore')
                files.append({
                    'path': content.path,
                    'content': file_content,
                    'size': content.size,
                    'sha': content.sha
                })
            except Exception as e:
                print(f"Error reading file {content.path}: {str(e)}")
        elif content.type == 'dir':
            # Recursively get directory contents
            try:
                dir_contents = repo.get_contents(content.path, ref=branch)
                files.extend(get_repo_contents_recursive(repo, dir_contents, branch, content.path))
            except Exception as e:
                print(f"Error reading directory {content.path}: {str(e)}")
    
    return files


def upload_to_s3(files: List[Dict], job_id: str, owner: str, repo: str) -> int:
    """
    Upload repository files to S3
    
    Returns: number of files uploaded
    """
    uploaded_count = 0
    
    for file_info in files:
        try:
            file_path = file_info['path']
            file_content = file_info['content']
            
            # S3 key: repos/{job_id}/{file_path}
            s3_key = f"repos/{job_id}/{file_path}"
            
            # Upload to S3
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=file_content.encode('utf-8') if isinstance(file_content, str) else file_content,
                ContentType='text/plain'  # Default, can be improved
            )
            
            uploaded_count += 1
            
        except Exception as e:
            print(f"Error uploading {file_info.get('path', 'unknown')} to S3: {str(e)}")
    
    print(f"Uploaded {uploaded_count} files to S3")
    return uploaded_count


def extract_languages(files: List[Dict]) -> List[str]:
    """Extract programming languages from file extensions"""
    language_extensions = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.jsx': 'JavaScript',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript',
        '.java': 'Java',
        '.cpp': 'C++',
        '.cc': 'C++',
        '.cxx': 'C++',
        '.hpp': 'C++',
        '.c': 'C',
        '.h': 'C',
        '.go': 'Go',
        '.rs': 'Rust',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.html': 'HTML',
        '.htm': 'HTML',
        '.css': 'CSS',
        '.scss': 'CSS',
        '.sh': 'Shell',
        '.bash': 'Shell',
        '.json': 'JSON',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.md': 'Markdown',
    }
    
    languages = set()
    
    for file_info in files:
        file_path = file_info['path']
        _, ext = os.path.splitext(file_path)
        if ext in language_extensions:
            languages.add(language_extensions[ext])
    
    return sorted(list(languages))


def build_file_structure(files: List[Dict]) -> Dict[str, Any]:
    """Build file tree structure"""
    structure = {}
    
    for file_info in files:
        file_path = file_info['path']
        parts = file_path.split('/')
        
        current = structure
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                # Last part is the file
                current[part] = {
                    'type': 'file',
                    'size': file_info.get('size', 0),
                    'path': file_path
                }
            else:
                # Directory
                if part not in current:
                    current[part] = {'type': 'directory', 'children': {}}
                current = current[part]['children']
    
    return structure


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Return standardized error response"""
    return {
        'statusCode': status_code,
        'body': json.dumps({
            'status': 'error',
            'message': message
        })
    }

