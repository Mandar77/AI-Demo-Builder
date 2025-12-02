"""
Service 2: README Parser
Parses README content and extracts structured information
"""

import json
import re
from typing import Dict, Any, List, Optional


def extract_title(readme: str) -> str:
    """
    Extract title from README (first H1 heading)
    
    Args:
        readme: README content
        
    Returns:
        Title string, or empty string if not found
    """
    # Match first H1 heading (# Title or Title with ===)
    patterns = [
        r'^#\s+(.+)$',  # # Title
        r'^(.+)\n={3,}$',  # Title\n===
    ]
    
    lines = readme.split('\n')
    for i, line in enumerate(lines[:10]):  # Check first 10 lines
        for pattern in patterns:
            match = re.match(pattern, line.strip())
            if match:
                title = match.group(1).strip()
                # Clean up: remove markdown links [text](url) -> text
                title = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', title)
                # Remove HTML entities and badges
                title = re.sub(r'&[^;]+;', '', title)  # Remove &middot; etc
                title = re.sub(r'!\[.*?\]\(.*?\)', '', title)  # Remove badges
                title = re.sub(r'\s+', ' ', title).strip()  # Clean whitespace
                return title
            # Check for underline style
            if i < len(lines) - 1:
                if re.match(r'^={3,}$', lines[i+1].strip()):
                    title = line.strip()
                    # Clean up title
                    title = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', title)
                    title = re.sub(r'&[^;]+;', '', title)
                    title = re.sub(r'!\[.*?\]\(.*?\)', '', title)
                    title = re.sub(r'\s+', ' ', title).strip()
                    return title
    
    return ""


def extract_features(readme: str) -> List[str]:
    """
    Extract features list from README
    
    Args:
        readme: README content
        
    Returns:
        List of feature strings
    """
    features = []
    
    # Look for Features section
    patterns = [
        r'(?:^##\s+Features?\s*$\n)(?:.*\n)*?((?:[-*+]|\d+\.)\s+.+?)(?=\n##|\Z)',
        r'(?:^###\s+Features?\s*$\n)(?:.*\n)*?((?:[-*+]|\d+\.)\s+.+?)(?=\n##|\Z)',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, readme, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        for match in matches:
            content = match.group(1)
            # Extract list items
            items = re.findall(r'[-*+]\s+(.+?)(?=\n[-*+]|\n\n|\Z)', content)
            features.extend([item.strip() for item in items if item.strip()])
    
    # Fallback 1: Find bullet points with bold format like "* **Feature:** description"
    if not features:
        # Look for patterns like "* **Declarative:** ..." or "* **Component-Based:** ..."
        bold_features = re.findall(r'^\*\s+\*\*([^:]+):\*\*', readme, re.MULTILINE)
        if bold_features:
            features.extend([f.strip() for f in bold_features if f.strip()])
    
    # Fallback 2: Find any bullet list near "feature" keyword
    if not features:
        lines = readme.split('\n')
        in_features_section = False
        for i, line in enumerate(lines):
            if 'feature' in line.lower() and ('##' in line or '###' in line):
                in_features_section = True
                continue
            if in_features_section:
                if line.strip().startswith(('#', '##')):
                    break
                match = re.match(r'[-*+]\s+(.+)', line)
                if match:
                    features.append(match.group(1).strip())
    
    # Fallback 3: If still no features, look for bullet points in first 50 lines
    # (common pattern: features listed right after title)
    if not features:
        lines = readme.split('\n')[:50]
        for line in lines:
            # Match "* **Feature:**" or "* Feature" patterns
            match = re.match(r'^\*\s+\*\*([^:]+):\*\*', line)
            if match:
                feature = match.group(1).strip()
                if len(feature) > 2 and len(feature) < 50:
                    features.append(feature)
            else:
                # Match simple "* Feature" if it's a short line (likely a feature)
                match = re.match(r'^\*\s+(.+)$', line)
                if match:
                    text = match.group(1).strip()
                    # Only add if it looks like a feature (not too long, no links)
                    if len(text) < 100 and not text.startswith('http'):
                        # Clean up markdown
                        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
                        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
                        if text and len(text) > 3:
                            features.append(text)
    
    return features[:10]  # Limit to first 10 features


def extract_installation(readme: str) -> str:
    """
    Extract installation instructions from README
    
    Args:
        readme: README content
        
    Returns:
        Installation instructions as string
    """
    # Look for Installation/Install section
    patterns = [
        r'(?:^##\s+Install(?:ation)?\s*$\n)(.*?)(?=\n##|\Z)',
        r'(?:^###\s+Install(?:ation)?\s*$\n)(.*?)(?=\n##|\Z)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, readme, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            # Take first few lines (usually code blocks or commands)
            lines = content.split('\n')[:10]
            return '\n'.join(lines).strip()
    
    return ""


def extract_usage(readme: str) -> str:
    """
    Extract usage examples from README
    
    Args:
        readme: README content
        
    Returns:
        Usage instructions as string
    """
    # Look for Usage section
    patterns = [
        r'(?:^##\s+Usage\s*$\n)(.*?)(?=\n##|\Z)',
        r'(?:^###\s+Usage\s*$\n)(.*?)(?=\n##|\Z)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, readme, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            # Take first 15 lines
            lines = content.split('\n')[:15]
            return '\n'.join(lines).strip()
    
    return ""


def check_documentation(readme: str) -> bool:
    """
    Check if README has substantial documentation
    
    Args:
        readme: README content
        
    Returns:
        True if README has good documentation, False otherwise
    """
    if not readme or len(readme.strip()) < 100:
        return False
    
    # Check for multiple sections (headings)
    heading_count = len(re.findall(r'^#+\s+', readme, re.MULTILINE))
    
    # Check for code blocks
    code_blocks = len(re.findall(r'```', readme))
    
    # Check for links
    links = len(re.findall(r'\[.+\]\(.+\)', readme))
    
    # Consider it documented if it has multiple sections or code examples
    return heading_count >= 3 or code_blocks >= 2 or links >= 3


def parse_readme(readme: str) -> Dict[str, Any]:
    """
    Parse README content and extract structured information
    
    Args:
        readme: README content as string
        
    Returns:
        Structured README data
    """
    if not readme:
        return {
            "title": "",
            "features": [],
            "installation": "",
            "usage": "",
            "hasDocumentation": False
        }
    
    result = {
        "title": extract_title(readme),
        "features": extract_features(readme),
        "installation": extract_installation(readme),
        "usage": extract_usage(readme),
        "hasDocumentation": check_documentation(readme)
    }
    
    return result


def process_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process the Lambda event and parse README content
    
    Args:
        event: Lambda event containing readme string
        
    Returns:
        Parsed README data
    """
    readme = event.get('readme', '')
    
    if not readme:
        return {
            "title": "",
            "features": [],
            "installation": "",
            "usage": "",
            "hasDocumentation": False
        }
    
    result = parse_readme(readme)
    print(f"[Service2] ✅ Successfully parsed README")
    print(f"[Service2]   Title: {result.get('title', 'N/A')}")
    print(f"[Service2]   Features found: {len(result.get('features', []))}")
    
    return result


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function
    
    Standard Lambda entry point for Service 2: README Parser
    
    Args:
        event: Input data containing readme string
        context: Lambda runtime context
        
    Returns:
        Standard Lambda response with statusCode and body
    """
    try:
        print(f"[Service2] Starting README parser service")
        result = process_request(event)
        
        return {
            "statusCode": 200,
            "body": result
        }
        
    except Exception as e:
        print(f"[Service2] ❌ Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": {"error": str(e)}
        }

