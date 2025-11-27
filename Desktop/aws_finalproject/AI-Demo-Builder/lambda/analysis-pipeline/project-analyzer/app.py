"""
Project Analyzer Lambda Function
Analyzes project structure, detects tech stack, frameworks, dependencies, and complexity
"""

import json
import os
import boto3
from typing import Dict, Any, List, Set
import re

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb_client = boto3.client('dynamodb')

# Environment variables
S3_BUCKET = os.environ.get('S3_BUCKET_NAME', 'ai-demo-builder-repos')
DYNAMODB_TABLE = os.environ.get('JOBS_TABLE_NAME', 'ai-demo-builder-jobs')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for Project Analyzer
    
    Expected event:
    {
        "job_id": "unique-job-id",
        "s3_location": "s3://bucket/path/to/repo"
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "status": "success",
            "job_id": "...",
            "analysis": {
                "tech_stack": ["Python", "JavaScript"],
                "frameworks": ["React", "FastAPI"],
                "dependencies": {...},
                "complexity": "Medium",
                "structure": {...},
                "file_stats": {...}
            }
        }
    }
    """
    try:
        # Extract input
        job_id = event.get('job_id')
        s3_location = event.get('s3_location')
        
        if not job_id or not s3_location:
            return error_response(400, "Missing required fields: job_id, s3_location")
        
        # Parse S3 location
        bucket, prefix = parse_s3_location(s3_location)
        
        # List all files in S3
        files = list_s3_files(bucket, prefix)
        
        # Analyze project
        analysis = analyze_project(bucket, prefix, files)
        
        # Update job status
        update_job_status(job_id, 'analysis_complete', {
            'project_analyzed': True,
            'tech_stack': analysis.get('tech_stack', []),
            'complexity': analysis.get('complexity', 'Unknown')
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'job_id': job_id,
                'analysis': analysis
            })
        }
        
    except Exception as e:
        print(f"Error in Project Analyzer: {str(e)}")
        return error_response(500, f"Internal error: {str(e)}")


def parse_s3_location(s3_location: str) -> tuple:
    """Parse S3 location string into bucket and prefix"""
    path = s3_location.replace('s3://', '')
    parts = path.split('/', 1)
    bucket = parts[0]
    prefix = parts[1] if len(parts) > 1 else ''
    if prefix and not prefix.endswith('/'):
        prefix += '/'
    return bucket, prefix


def list_s3_files(bucket: str, prefix: str) -> List[Dict[str, Any]]:
    """List all files in S3 location"""
    files = []
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    # Remove prefix to get relative path
                    relative_path = key.replace(prefix, '')
                    if relative_path:  # Skip empty paths
                        files.append({
                            'key': key,
                            'path': relative_path,
                            'size': obj['Size']
                        })
    except Exception as e:
        print(f"Error listing S3 files: {str(e)}")
    
    return files


def analyze_project(bucket: str, prefix: str, files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze project structure, tech stack, frameworks, and dependencies
    
    Returns:
    {
        "tech_stack": [...],
        "frameworks": [...],
        "dependencies": {...},
        "complexity": "...",
        "structure": {...},
        "file_stats": {...}
    }
    """
    # Extract tech stack from file extensions
    tech_stack = detect_tech_stack(files)
    
    # Detect frameworks
    frameworks = detect_frameworks(bucket, prefix, files)
    
    # Extract dependencies
    dependencies = extract_dependencies(bucket, prefix, files)
    
    # Analyze project structure
    structure = analyze_structure(files)
    
    # Calculate file statistics
    file_stats = calculate_file_stats(files)
    
    # Assess complexity
    complexity = assess_complexity(files, tech_stack, frameworks, dependencies)
    
    return {
        'tech_stack': tech_stack,
        'frameworks': frameworks,
        'dependencies': dependencies,
        'complexity': complexity,
        'structure': structure,
        'file_stats': file_stats
    }


def detect_tech_stack(files: List[Dict[str, Any]]) -> List[str]:
    """Detect programming languages from file extensions"""
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
        '.sass': 'CSS',
        '.less': 'CSS',
        '.sql': 'SQL',
        '.sh': 'Shell',
        '.bash': 'Shell',
        '.ps1': 'PowerShell',
        '.r': 'R',
        '.m': 'Objective-C',
        '.mm': 'Objective-C++',
        '.dart': 'Dart',
        '.lua': 'Lua',
        '.pl': 'Perl',
        '.pm': 'Perl',
        '.clj': 'Clojure',
        '.hs': 'Haskell',
        '.elm': 'Elm',
        '.ex': 'Elixir',
        '.exs': 'Elixir',
        '.ml': 'OCaml',
        '.fs': 'F#',
        '.vb': 'VB.NET',
        '.cs': 'C#',
        '.d': 'D',
        '.nim': 'Nim',
        '.zig': 'Zig',
    }
    
    languages = set()
    for file_info in files:
        path = file_info.get('path', '')
        _, ext = os.path.splitext(path.lower())
        if ext in language_extensions:
            languages.add(language_extensions[ext])
    
    return sorted(list(languages))


def detect_frameworks(bucket: str, prefix: str, files: List[Dict[str, Any]]) -> List[str]:
    """Detect frameworks from configuration files and project structure"""
    frameworks = set()
    
    # Framework detection patterns
    framework_indicators = {
        'package.json': ['react', 'vue', 'angular', 'express', 'next', 'nuxt', 'svelte'],
        'requirements.txt': ['django', 'flask', 'fastapi', 'tornado', 'bottle'],
        'pom.xml': ['spring', 'hibernate', 'maven'],
        'build.gradle': ['spring', 'android'],
        'Cargo.toml': ['actix', 'rocket', 'tokio'],
        'go.mod': ['gin', 'echo', 'fiber'],
        'composer.json': ['laravel', 'symfony', 'codeigniter'],
        'Gemfile': ['rails', 'sinatra'],
        'mix.exs': ['phoenix'],
        'dub.json': ['vibe'],
    }
    
    # Check for framework-specific files and patterns
    file_paths = [f.get('path', '').lower() for f in files]
    
    # React/Vue/Angular detection
    if any('package.json' in path for path in file_paths):
        for file_info in files:
            if 'package.json' in file_info.get('path', '').lower():
                content = download_from_s3(bucket, file_info['key'])
                if content:
                    try:
                        pkg = json.loads(content)
                        deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
                        dep_names = [dep.lower() for dep in deps.keys()]
                        
                        if any('react' in d for d in dep_names):
                            frameworks.add('React')
                        if any('vue' in d for d in dep_names):
                            frameworks.add('Vue.js')
                        if any('angular' in d for d in dep_names):
                            frameworks.add('Angular')
                        if any('next' in d for d in dep_names):
                            frameworks.add('Next.js')
                        if any('express' in d for d in dep_names):
                            frameworks.add('Express')
                        if any('svelte' in d for d in dep_names):
                            frameworks.add('Svelte')
                    except:
                        pass
    
    # Python frameworks
    if any('requirements.txt' in path for path in file_paths):
        for file_info in files:
            if 'requirements.txt' in file_info.get('path', '').lower():
                content = download_from_s3(bucket, file_info['key'])
                if content:
                    content_lower = content.lower()
                    if 'django' in content_lower:
                        frameworks.add('Django')
                    if 'flask' in content_lower:
                        frameworks.add('Flask')
                    if 'fastapi' in content_lower:
                        frameworks.add('FastAPI')
                    if 'tornado' in content_lower:
                        frameworks.add('Tornado')
    
    # Java frameworks
    if any('pom.xml' in path for path in file_paths):
        frameworks.add('Maven')
        for file_info in files:
            if 'pom.xml' in file_info.get('path', '').lower():
                content = download_from_s3(bucket, file_info['key'])
                if content and 'spring' in content.lower():
                    frameworks.add('Spring')
    
    # Go frameworks
    if any('go.mod' in path for path in file_paths):
        for file_info in files:
            if 'go.mod' in file_info.get('path', '').lower():
                content = download_from_s3(bucket, file_info['key'])
                if content:
                    if 'gin' in content.lower():
                        frameworks.add('Gin')
                    if 'echo' in content.lower():
                        frameworks.add('Echo')
    
    # Rust frameworks
    if any('cargo.toml' in path for path in file_paths):
        frameworks.add('Cargo')
        for file_info in files:
            if 'cargo.toml' in file_info.get('path', '').lower():
                content = download_from_s3(bucket, file_info['key'])
                if content:
                    if 'actix' in content.lower():
                        frameworks.add('Actix')
                    if 'rocket' in content.lower():
                        frameworks.add('Rocket')
    
    # Check for framework-specific directories
    dirs = set()
    for file_info in files:
        path = file_info.get('path', '')
        dir_parts = path.split('/')
        if len(dir_parts) > 1:
            dirs.add(dir_parts[0])
    
    if 'src' in dirs and 'components' in dirs:
        frameworks.add('React')  # Likely React project
    
    return sorted(list(frameworks))


def extract_dependencies(bucket: str, prefix: str, files: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Extract dependencies from various dependency files"""
    dependencies = {}
    
    for file_info in files:
        path = file_info.get('path', '').lower()
        
        # Python requirements.txt
        if 'requirements.txt' in path:
            content = download_from_s3(bucket, file_info['key'])
            if content:
                deps = [line.strip() for line in content.split('\n') 
                       if line.strip() and not line.startswith('#')]
                dependencies['python'] = deps
        
        # Node.js package.json
        elif 'package.json' in path:
            content = download_from_s3(bucket, file_info['key'])
            if content:
                try:
                    pkg = json.loads(content)
                    deps = list(pkg.get('dependencies', {}).keys())
                    dev_deps = list(pkg.get('devDependencies', {}).keys())
                    dependencies['nodejs'] = deps + dev_deps
                except:
                    pass
        
        # Java pom.xml
        elif 'pom.xml' in path:
            content = download_from_s3(bucket, file_info['key'])
            if content:
                # Simple regex extraction (could be improved with XML parser)
                deps = re.findall(r'<artifactId>([^<]+)</artifactId>', content)
                dependencies['java'] = deps[:20]  # Limit to first 20
        
        # Go go.mod
        elif 'go.mod' in path:
            content = download_from_s3(bucket, file_info['key'])
            if content:
                deps = [line.strip().split()[0] for line in content.split('\n')
                       if line.strip() and not line.startswith('module') 
                       and not line.startswith('go ') and not line.startswith('//')]
                dependencies['go'] = deps
        
        # Rust Cargo.toml
        elif 'cargo.toml' in path:
            content = download_from_s3(bucket, file_info['key'])
            if content:
                deps = re.findall(r'(\w+)\s*=', content)
                dependencies['rust'] = deps[:20]  # Limit to first 20
        
        # PHP composer.json
        elif 'composer.json' in path:
            content = download_from_s3(bucket, file_info['key'])
            if content:
                try:
                    composer = json.loads(content)
                    deps = list(composer.get('require', {}).keys())
                    dependencies['php'] = deps
                except:
                    pass
        
        # Ruby Gemfile
        elif 'gemfile' in path:
            content = download_from_s3(bucket, file_info['key'])
            if content:
                deps = [line.strip().replace("'", '').replace('"', '') 
                       for line in content.split('\n')
                       if 'gem' in line.lower() and not line.strip().startswith('#')]
                dependencies['ruby'] = deps
    
    return dependencies


def analyze_structure(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze project directory structure"""
    structure = {
        'directories': [],
        'depth': 0,
        'has_tests': False,
        'has_docs': False,
        'has_config': False
    }
    
    dirs = set()
    max_depth = 0
    
    for file_info in files:
        path = file_info.get('path', '')
        path_lower = path.lower()
        
        # Check for test directories
        if any(test_dir in path_lower for test_dir in ['test', 'tests', '__tests__', 'spec', 'specs']):
            structure['has_tests'] = True
        
        # Check for documentation
        if any(doc_file in path_lower for doc_file in ['readme', 'docs', 'documentation']):
            structure['has_docs'] = True
        
        # Check for config files
        if any(config_dir in path_lower for config_dir in ['.config', 'config', 'settings']):
            structure['has_config'] = True
        
        # Extract directory structure
        parts = path.split('/')
        depth = len(parts) - 1
        max_depth = max(max_depth, depth)
        
        for i in range(1, len(parts)):
            dir_path = '/'.join(parts[:i])
            dirs.add(dir_path)
    
    structure['directories'] = sorted(list(dirs))[:50]  # Limit to first 50
    structure['depth'] = max_depth
    
    return structure


def calculate_file_stats(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate file statistics"""
    total_files = len(files)
    total_size = sum(f.get('size', 0) for f in files)
    
    # Count by extension
    ext_counts = {}
    for file_info in files:
        _, ext = os.path.splitext(file_info.get('path', ''))
        ext = ext.lower() if ext else 'no_extension'
        ext_counts[ext] = ext_counts.get(ext, 0) + 1
    
    # Top extensions
    top_extensions = sorted(ext_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        'total_files': total_files,
        'total_size_bytes': total_size,
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'top_extensions': [{'extension': ext, 'count': count} for ext, count in top_extensions]
    }


def assess_complexity(files: List[Dict[str, Any]], tech_stack: List[str], 
                     frameworks: List[str], dependencies: Dict[str, List[str]]) -> str:
    """Assess project complexity based on various factors"""
    score = 0
    
    # File count factor
    file_count = len(files)
    if file_count < 10:
        score += 1
    elif file_count < 50:
        score += 2
    elif file_count < 200:
        score += 3
    else:
        score += 4
    
    # Tech stack diversity
    if len(tech_stack) == 1:
        score += 1
    elif len(tech_stack) <= 3:
        score += 2
    else:
        score += 3
    
    # Framework count
    if len(frameworks) == 0:
        score += 1
    elif len(frameworks) <= 2:
        score += 2
    else:
        score += 3
    
    # Dependency count
    total_deps = sum(len(deps) for deps in dependencies.values())
    if total_deps < 5:
        score += 1
    elif total_deps < 20:
        score += 2
    elif total_deps < 50:
        score += 3
    else:
        score += 4
    
    # Determine complexity level
    if score <= 5:
        return 'Low'
    elif score <= 8:
        return 'Medium'
    elif score <= 11:
        return 'High'
    else:
        return 'Very High'


def download_from_s3(bucket: str, key: str) -> str:
    """Download file content from S3"""
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read().decode('utf-8')
    except Exception as e:
        print(f"Error downloading {key} from S3: {str(e)}")
        return None


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


