"""
Local test script for Service 2: README Parser
Can be run directly without AWS Lambda environment
"""

from readme_parser import lambda_handler


def test_readme_parser():
    """Test the README parser with sample content"""
    
    print("=" * 60)
    print("Testing Service 2: README Parser")
    print("=" * 60)
    
    # Test case 1: Well-structured README
    print("\n📦 Test Case 1: Parsing structured README")
    sample_readme = """# My Awesome Project

A description of the project goes here.

## Features

- Feature 1: Fast performance
- Feature 2: Easy to use
- Feature 3: Well documented

## Installation

```bash
npm install my-project
```

Or using pip:

```bash
pip install my-project
```

## Usage

```python
import my_project

result = my_project.doSomething()
```

## Documentation

Check out our docs at https://example.com/docs
"""
    
    event = {
        "readme": sample_readme
    }
    
    result = lambda_handler(event, None)
    
    print(f"\nStatus Code: {result['statusCode']}")
    
    if result['statusCode'] == 200:
        body = result['body']
        print(f"✅ Test passed!")
        print(f"   Title: {body.get('title')}")
        print(f"   Features: {body.get('features')}")
        print(f"   Has Installation: {bool(body.get('installation'))}")
        print(f"   Has Usage: {bool(body.get('usage'))}")
        print(f"   Has Documentation: {body.get('hasDocumentation')}")
    else:
        print(f"❌ Test failed: {result.get('body', {})}")
    
    # Test case 2: Empty README
    print("\n📦 Test Case 2: Empty README")
    event_empty = {
        "readme": ""
    }
    
    result_empty = lambda_handler(event_empty, None)
    print(f"Status Code: {result_empty['statusCode']}")
    
    if result_empty['statusCode'] == 200:
        body_empty = result_empty['body']
        print(f"✅ Empty README handled correctly!")
        print(f"   Title: '{body_empty.get('title')}'")
        print(f"   Features count: {len(body_empty.get('features', []))}")
    else:
        print(f"❌ Expected 200, got {result_empty['statusCode']}")
    
    # Test case 3: Missing readme field
    print("\n📦 Test Case 3: Missing readme field")
    event_missing = {}
    
    result_missing = lambda_handler(event_missing, None)
    print(f"Status Code: {result_missing['statusCode']}")
    
    if result_missing['statusCode'] == 200:
        print(f"✅ Missing field handled gracefully!")
    else:
        print(f"❌ Expected 200, got {result_missing['statusCode']}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_readme_parser()

