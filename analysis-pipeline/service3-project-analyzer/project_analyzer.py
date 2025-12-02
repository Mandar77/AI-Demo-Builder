"""
Service 3: Project Analyzer
Analyzes project type and complexity based on GitHub data and parsed README
"""

from typing import Dict, Any, List


def determine_project_type(github_data: Dict[str, Any], parsed_readme: Dict[str, Any]) -> str:
    """
    Determine project type based on repository data and README
    
    Args:
        github_data: Repository information from Service 1
        parsed_readme: Parsed README data from Service 2
        
    Returns:
        Project type string (e.g., "library", "application", "framework", etc.)
    """
    # Check topics for hints
    topics = github_data.get('topics', [])
    topic_lower = [t.lower() for t in topics]
    
    # Check README for keywords
    readme_features = ' '.join(parsed_readme.get('features', [])).lower()
    readme_title = parsed_readme.get('title', '').lower()
    
    all_text = ' '.join([readme_features, readme_title, ' '.join(topic_lower)]).lower()
    
    # Framework indicators
    if any(keyword in all_text for keyword in ['framework', 'ui framework', 'react', 'vue', 'angular']):
        return "framework"
    
    # Library indicators
    if any(keyword in all_text for keyword in ['library', 'sdk', 'api client', 'wrapper']):
        return "library"
    
    # CLI tool indicators
    if any(keyword in all_text for keyword in ['cli', 'command line', 'tool', 'utility']):
        return "cli-tool"
    
    # Application indicators
    if any(keyword in all_text for keyword in ['app', 'application', 'web app', 'desktop app']):
        return "application"
    
    # Plugin/Extension indicators
    if any(keyword in all_text for keyword in ['plugin', 'extension', 'addon']):
        return "plugin"
    
    # Default: library if it's a code repository
    if github_data.get('language'):
        return "library"
    
    return "unknown"


def determine_complexity(github_data: Dict[str, Any], parsed_readme: Dict[str, Any]) -> str:
    """
    Determine project complexity level
    
    Args:
        github_data: Repository information from Service 1
        parsed_readme: Parsed README data from Service 2
        
    Returns:
        Complexity level: "low", "medium", or "high"
    """
    score = 0
    
    # Stars as complexity indicator (popular projects tend to be more complex)
    stars = github_data.get('stars', 0)
    if stars > 10000:
        score += 3
    elif stars > 1000:
        score += 2
    elif stars > 100:
        score += 1
    
    # Number of features
    features_count = len(parsed_readme.get('features', []))
    if features_count > 10:
        score += 2
    elif features_count > 5:
        score += 1
    
    # Documentation quality
    if parsed_readme.get('hasDocumentation'):
        score += 1
    
    # Has installation and usage sections (indicates more structured project)
    if parsed_readme.get('installation'):
        score += 1
    if parsed_readme.get('usage'):
        score += 1
    
    # Determine complexity
    if score >= 5:
        return "high"
    elif score >= 3:
        return "medium"
    else:
        return "low"


def extract_tech_stack(github_data: Dict[str, Any], parsed_readme: Dict[str, Any]) -> List[str]:
    """
    Extract technology stack information
    
    Args:
        github_data: Repository information from Service 1
        parsed_readme: Parsed README data from Service 2
        
    Returns:
        List of technology names
    """
    tech_stack = []
    
    # Add primary language
    language = github_data.get('language', '')
    if language:
        tech_stack.append(language)
    
    # Extract from topics
    topics = github_data.get('topics', [])
    common_tech = ['react', 'vue', 'angular', 'nodejs', 'python', 'typescript', 
                   'docker', 'kubernetes', 'aws', 'gcp', 'azure', 'postgresql',
                   'mongodb', 'redis', 'graphql', 'rest']
    
    for topic in topics:
        topic_lower = topic.lower()
        # Check if topic matches known technologies
        for tech in common_tech:
            if tech in topic_lower:
                if tech not in tech_stack:
                    tech_stack.append(tech.capitalize())
    
    # Extract from README features
    features = ' '.join(parsed_readme.get('features', [])).lower()
    for tech in common_tech:
        if tech in features and tech.capitalize() not in tech_stack:
            tech_stack.append(tech.capitalize())
    
    return tech_stack[:10]  # Limit to 10 technologies


def extract_key_features(parsed_readme: Dict[str, Any]) -> List[str]:
    """
    Extract key features from parsed README
    
    Args:
        parsed_readme: Parsed README data from Service 2
        
    Returns:
        List of key feature strings
    """
    features = parsed_readme.get('features', [])
    # Return first 5 features as key features
    return features[:5]


def calculate_suggested_segments(complexity: str, project_type: str) -> int:
    """
    Calculate suggested number of segments for project breakdown
    
    Args:
        complexity: Project complexity level
        project_type: Type of project
        
    Returns:
        Suggested number of segments (1-10)
    """
    base_segments = {
        "low": 2,
        "medium": 4,
        "high": 6
    }
    
    type_modifier = {
        "framework": 2,
        "library": 1,
        "application": 3,
        "cli-tool": 1,
        "plugin": 1,
        "unknown": 1
    }
    
    segments = base_segments.get(complexity, 3) + type_modifier.get(project_type, 0)
    
    # Clamp between 1 and 10
    return max(1, min(10, segments))


def process_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process the Lambda event and analyze project
    
    Args:
        event: Lambda event containing github_data and parsed_readme
        
    Returns:
        Project analysis results
    """
    github_data = event.get('github_data', {})
    parsed_readme = event.get('parsed_readme', {})
    
    # Validate required data
    if not github_data:
        raise ValueError("Missing required field: github_data")
    if not parsed_readme:
        raise ValueError("Missing required field: parsed_readme")
    
    # Perform analysis
    project_type = determine_project_type(github_data, parsed_readme)
    complexity = determine_complexity(github_data, parsed_readme)
    tech_stack = extract_tech_stack(github_data, parsed_readme)
    key_features = extract_key_features(parsed_readme)
    suggested_segments = calculate_suggested_segments(complexity, project_type)
    
    result = {
        "projectType": project_type,
        "complexity": complexity,
        "techStack": tech_stack,
        "keyFeatures": key_features,
        "suggestedSegments": suggested_segments
    }
    
    print(f"[Service3] ✅ Successfully analyzed project")
    print(f"[Service3]   Type: {project_type}")
    print(f"[Service3]   Complexity: {complexity}")
    print(f"[Service3]   Tech Stack: {tech_stack}")
    
    return result


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function
    
    Standard Lambda entry point for Service 3: Project Analyzer
    
    Args:
        event: Input data containing github_data and parsed_readme
        context: Lambda runtime context
        
    Returns:
        Standard Lambda response with statusCode and body
    """
    try:
        print(f"[Service3] Starting project analyzer service")
        result = process_request(event)
        
        return {
            "statusCode": 200,
            "body": result
        }
        
    except ValueError as e:
        print(f"[Service3] ❌ Validation Error: {str(e)}")
        return {
            "statusCode": 400,
            "body": {"error": str(e)}
        }
        
    except Exception as e:
        print(f"[Service3] ❌ Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": {"error": str(e)}
        }

