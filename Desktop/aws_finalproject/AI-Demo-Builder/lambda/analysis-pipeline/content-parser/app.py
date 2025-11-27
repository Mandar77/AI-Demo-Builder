"""
README Parser Lambda Function
Parses README files and extracts structured information
"""

import json
import os
import boto3
from typing import Dict, Any, List
import markdown
from bs4 import BeautifulSoup

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb_client = boto3.client('dynamodb')

# Environment variables
S3_BUCKET = os.environ.get('S3_BUCKET_NAME', 'ai-demo-builder-repos')
DYNAMODB_TABLE = os.environ.get('JOBS_TABLE_NAME', 'ai-demo-builder-jobs')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for README Parser
    
    Expected event:
    {
        "job_id": "unique-job-id",
        "s3_location": "s3://bucket/path/to/repo",
        "readme_files": ["README.md"] (optional)
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "status": "success",
            "job_id": "...",
            "parsed_content": {
                "description": "...",
                "installation": "...",
                "usage": "...",
                "features": [...],
                "dependencies": [...]
            }
        }
    }
    """
    try:
        # Extract input
        job_id = event.get('job_id')
        s3_location = event.get('s3_location')
        readme_files = event.get('readme_files', [])
        
        if not job_id or not s3_location:
            return error_response(400, "Missing required fields: job_id, s3_location")
        
        # Parse S3 location
        bucket, prefix = parse_s3_location(s3_location)
        
        # Find README files if not provided
        if not readme_files:
            readme_files = find_readme_files(bucket, prefix)
        
        # Parse README files
        parsed_content = {}
        for readme_file in readme_files:
            content = download_from_s3(bucket, f"{prefix}{readme_file}")
            if content:
                parsed = parse_markdown(content)
                parsed_content[readme_file] = parsed
        
        # Combine all parsed content
        combined = combine_parsed_content(list(parsed_content.values()))
        
        # Update job status
        update_job_status(job_id, 'parsing_complete', {
            'readme_parsed': True,
            'parsed_files': list(parsed_content.keys())
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'job_id': job_id,
                'parsed_content': combined,
                'files_parsed': list(parsed_content.keys())
            })
        }
        
    except Exception as e:
        print(f"Error in README Parser: {str(e)}")
        return error_response(500, f"Internal error: {str(e)}")


def parse_s3_location(s3_location: str) -> tuple:
    """Parse S3 location string into bucket and prefix"""
    # Remove s3:// prefix
    path = s3_location.replace('s3://', '')
    parts = path.split('/', 1)
    bucket = parts[0]
    prefix = parts[1] if len(parts) > 1 else ''
    if prefix and not prefix.endswith('/'):
        prefix += '/'
    return bucket, prefix


def find_readme_files(bucket: str, prefix: str) -> List[str]:
    """Find all README files in S3 location"""
    readme_files = []
    readme_patterns = ['README.md', 'README.txt', 'readme.md', 'README']
    
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        if 'Contents' in response:
            for obj in response['Contents']:
                key = obj['Key']
                filename = key.replace(prefix, '')
                # Check if it's a README file
                for pattern in readme_patterns:
                    if filename == pattern or filename.lower().endswith(pattern.lower()):
                        readme_files.append(filename)
                        break
    except Exception as e:
        print(f"Error finding README files: {str(e)}")
    
    return readme_files


def download_from_s3(bucket: str, key: str) -> str:
    """Download file content from S3"""
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read().decode('utf-8')
    except Exception as e:
        print(f"Error downloading from S3: {str(e)}")
        return None


def parse_markdown(content: str) -> Dict[str, Any]:
    """
    Parse markdown content and extract structured information
    
    Returns:
    {
        "description": "...",
        "installation": "...",
        "usage": "...",
        "features": [...],
        "dependencies": [...]
    }
    """
    # Convert markdown to HTML
    html = markdown.markdown(content, extensions=['extra', 'codehilite'])
    soup = BeautifulSoup(html, 'html.parser')
    
    parsed = {
        'description': extract_description(soup),
        'installation': extract_section(soup, ['installation', 'install', 'setup']),
        'usage': extract_section(soup, ['usage', 'use', 'example', 'examples']),
        'features': extract_list_items(soup, ['features', 'feature', 'key features']),
        'dependencies': extract_dependencies(content)
    }
    
    return parsed


def extract_description(soup: BeautifulSoup) -> str:
    """Extract project description (first paragraph)"""
    first_p = soup.find('p')
    return first_p.get_text().strip() if first_p else ""


def extract_section(soup: BeautifulSoup, section_names: List[str]) -> str:
    """Extract content from a section by header name"""
    for name in section_names:
        # Find headers (h1-h3) containing section name
        headers = soup.find_all(['h1', 'h2', 'h3'], string=lambda text: name.lower() in text.lower() if text else False)
        if headers:
            section_content = []
            header = headers[0]
            # Get all siblings until next header
            for sibling in header.next_siblings:
                if sibling.name and sibling.name in ['h1', 'h2', 'h3']:
                    break
                if sibling.name:
                    section_content.append(sibling.get_text())
            return '\n'.join(section_content)
    return ""


def extract_list_items(soup: BeautifulSoup, section_names: List[str]) -> List[str]:
    """Extract list items from a section"""
    for name in section_names:
        headers = soup.find_all(['h1', 'h2', 'h3'], string=lambda text: name.lower() in text.lower() if text else False)
        if headers:
            header = headers[0]
            # Find next list
            for sibling in header.next_siblings:
                if sibling.name == 'ul':
                    return [li.get_text().strip() for li in sibling.find_all('li')]
    return []


def extract_dependencies(content: str) -> List[str]:
    """Extract dependencies from content (looks for requirements.txt patterns)"""
    dependencies = []
    lines = content.split('\n')
    in_dependencies = False
    
    for line in lines:
        if any(keyword in line.lower() for keyword in ['dependencies', 'requirements', 'install']):
            in_dependencies = True
            continue
        if in_dependencies:
            # Check if line looks like a dependency
            if line.strip() and not line.startswith('#'):
                dependencies.append(line.strip())
            if line.strip() == '' and dependencies:  # Empty line after dependencies
                break
    
    return dependencies


def combine_parsed_content(parsed_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Combine parsed content from multiple README files"""
    combined = {
        'description': '',
        'installation': '',
        'usage': '',
        'features': [],
        'dependencies': []
    }
    
    for parsed in parsed_list:
        if parsed.get('description'):
            combined['description'] += parsed['description'] + '\n\n'
        if parsed.get('installation'):
            combined['installation'] += parsed['installation'] + '\n\n'
        if parsed.get('usage'):
            combined['usage'] += parsed['usage'] + '\n\n'
        combined['features'].extend(parsed.get('features', []))
        combined['dependencies'].extend(parsed.get('dependencies', []))
    
    # Remove duplicates
    combined['features'] = list(set(combined['features']))
    combined['dependencies'] = list(set(combined['dependencies']))
    
    # Clean up whitespace
    combined['description'] = combined['description'].strip()
    combined['installation'] = combined['installation'].strip()
    combined['usage'] = combined['usage'].strip()
    
    return combined


def update_job_status(job_id: str, status: str, metadata: Dict[str, Any]):
    """Update job status in DynamoDB"""
    try:
        dynamodb_client.update_item(
            TableName=DYNAMODB_TABLE,
            Key={'jobId': {'S': job_id}},
            UpdateExpression='SET #status = :status, #metadata = :metadata',
            ExpressionAttributeNames={
                '#status': 'status',
                '#metadata': 'metadata'
            },
            ExpressionAttributeValues={
                ':status': {'S': status},
                ':metadata': {'S': json.dumps(metadata)}
            }
        )
    except Exception as e:
        print(f"Failed to update job status: {str(e)}")


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Return standardized error response"""
    return {
        'statusCode': status_code,
        'body': json.dumps({
            'status': 'error',
            'message': message
        })
    }

