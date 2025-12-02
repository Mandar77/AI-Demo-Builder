"""
Local test script for Service 1: GitHub Fetcher
Can be run directly without AWS Lambda environment
"""

import json
import os
from github_fetcher import lambda_handler

# Set up test environment variables (optional)
# For local testing, you can set GITHUB_TOKEN here or use environment variable
# os.environ['GITHUB_TOKEN'] = 'your_token_here'

def test_github_fetcher():
    """Test the GitHub fetcher with a real repository"""
    
    print("=" * 60)
    print("Testing Service 1: GitHub Repository Fetcher")
    print("=" * 60)
    
    # Test case 1: Fetch a well-known repository
    print("\n📦 Test Case 1: Fetching facebook/react")
    event = {
        "github_url": "https://github.com/facebook/react"
    }
    
    result = lambda_handler(event, None)
    
    print(f"\nStatus Code: {result['statusCode']}")
    print(f"Response Body Keys: {list(result.get('body', {}).keys())}")
    
    if result['statusCode'] == 200:
        body = result['body']
        print(f"✅ Test passed!")
        print(f"   Project Name: {body.get('projectName')}")
        print(f"   Owner: {body.get('owner')}")
        print(f"   Stars: {body.get('stars')}")
        print(f"   Language: {body.get('language')}")
        print(f"   README length: {len(body.get('readme', ''))} characters")
    else:
        print(f"❌ Test failed: {result.get('body', {})}")
    
    # Test case 2: Invalid URL
    print("\n📦 Test Case 2: Invalid GitHub URL")
    event_invalid = {
        "github_url": "https://invalid-url.com"
    }
    
    result_invalid = lambda_handler(event_invalid, None)
    print(f"Status Code: {result_invalid['statusCode']}")
    
    if result_invalid['statusCode'] == 400:
        print(f"✅ Validation error handling works!")
    else:
        print(f"❌ Expected 400, got {result_invalid['statusCode']}")
    
    # Test case 3: Missing field
    print("\n📦 Test Case 3: Missing github_url field")
    event_missing = {}
    
    result_missing = lambda_handler(event_missing, None)
    print(f"Status Code: {result_missing['statusCode']}")
    
    if result_missing['statusCode'] == 400:
        print(f"✅ Missing field validation works!")
    else:
        print(f"❌ Expected 400, got {result_missing['statusCode']}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_github_fetcher()

