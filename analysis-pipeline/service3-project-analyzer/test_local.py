"""
Local test script for Service 3: Project Analyzer
Can be run directly without AWS Lambda environment
"""

from project_analyzer import lambda_handler


def test_project_analyzer():
    """Test the project analyzer with sample data"""
    
    print("=" * 60)
    print("Testing Service 3: Project Analyzer")
    print("=" * 60)
    
    # Test case 1: Well-known project (React-like)
    print("\n📦 Test Case 1: Analyzing a framework project")
    
    github_data = {
        "stars": 200000,
        "language": "JavaScript",
        "topics": ["ui", "frontend", "react", "virtual-dom"]
    }
    
    parsed_readme = {
        "features": [
            "Virtual DOM for efficient rendering",
            "Component-based architecture",
            "JSX syntax",
            "One-way data binding",
            "React Hooks",
            "Server-side rendering"
        ],
        "hasDocumentation": True,
        "installation": "npm install react",
        "usage": "import React from 'react'"
    }
    
    event = {
        "github_data": github_data,
        "parsed_readme": parsed_readme
    }
    
    result = lambda_handler(event, None)
    
    print(f"\nStatus Code: {result['statusCode']}")
    
    if result['statusCode'] == 200:
        body = result['body']
        print(f"✅ Test passed!")
        print(f"   Project Type: {body.get('projectType')}")
        print(f"   Complexity: {body.get('complexity')}")
        print(f"   Tech Stack: {body.get('techStack')}")
        print(f"   Key Features: {body.get('keyFeatures')}")
        print(f"   Suggested Segments: {body.get('suggestedSegments')}")
    else:
        print(f"❌ Test failed: {result.get('body', {})}")
    
    # Test case 2: Simple library
    print("\n📦 Test Case 2: Analyzing a simple library")
    
    github_data_simple = {
        "stars": 150,
        "language": "Python",
        "topics": ["utility", "helper"]
    }
    
    parsed_readme_simple = {
        "features": [
            "Simple API",
            "Easy to use"
        ],
        "hasDocumentation": False,
        "installation": "pip install mylib",
        "usage": ""
    }
    
    event_simple = {
        "github_data": github_data_simple,
        "parsed_readme": parsed_readme_simple
    }
    
    result_simple = lambda_handler(event_simple, None)
    
    print(f"Status Code: {result_simple['statusCode']}")
    
    if result_simple['statusCode'] == 200:
        body_simple = result_simple['body']
        print(f"✅ Simple project analyzed!")
        print(f"   Project Type: {body_simple.get('projectType')}")
        print(f"   Complexity: {body_simple.get('complexity')}")
        print(f"   Suggested Segments: {body_simple.get('suggestedSegments')}")
    else:
        print(f"❌ Test failed: {result_simple.get('body', {})}")
    
    # Test case 3: Missing required fields
    print("\n📦 Test Case 3: Missing required fields")
    
    event_missing = {
        "github_data": {}
    }
    
    result_missing = lambda_handler(event_missing, None)
    print(f"Status Code: {result_missing['statusCode']}")
    
    if result_missing['statusCode'] == 400:
        print(f"✅ Validation error handling works!")
    else:
        print(f"❌ Expected 400, got {result_missing['statusCode']}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_project_analyzer()

