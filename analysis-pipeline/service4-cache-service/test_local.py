"""
Local test script for Service 4: Cache Service
Note: This requires local DynamoDB or mocking for full testing
"""

import json
from cache_service import lambda_handler

# For local testing, you might want to use DynamoDB Local or mock boto3
# This is a basic test that will fail if DynamoDB is not available


def test_cache_service():
    """Test the cache service"""
    
    print("=" * 60)
    print("Testing Service 4: Cache Service")
    print("=" * 60)
    print("\n⚠️  Note: This test requires DynamoDB table or mocking")
    print("    Set DYNAMODB_TABLE environment variable if needed\n")
    
    # Test case 1: Set operation
    print("📦 Test Case 1: Setting cache item")
    event_set = {
        "operation": "set",
        "key": "test_key_123",
        "value": {
            "projectName": "test-project",
            "stars": 1000
        }
    }
    
    result_set = lambda_handler(event_set, None)
    print(f"Status Code: {result_set['statusCode']}")
    
    if result_set['statusCode'] == 200:
        print(f"✅ Set operation successful!")
        print(f"   Response: {result_set.get('body', {})}")
    elif result_set['statusCode'] == 503:
        print(f"⚠️  DynamoDB table not found (expected in local testing)")
        print(f"   Error: {result_set.get('body', {}).get('error', 'Unknown error')}")
    else:
        print(f"❌ Set operation failed: {result_set.get('body', {})}")
    
    # Test case 2: Get operation
    print("\n📦 Test Case 2: Getting cache item")
    event_get = {
        "operation": "get",
        "key": "test_key_123"
    }
    
    result_get = lambda_handler(event_get, None)
    print(f"Status Code: {result_get['statusCode']}")
    
    if result_get['statusCode'] == 200:
        body = result_get.get('body', {})
        print(f"✅ Get operation successful!")
        print(f"   Found: {body.get('found')}")
        if body.get('found'):
            print(f"   Value: {body.get('value')}")
    elif result_get['statusCode'] == 503:
        print(f"⚠️  DynamoDB table not found (expected in local testing)")
    else:
        print(f"❌ Get operation failed: {result_get.get('body', {})}")
    
    # Test case 3: Delete operation
    print("\n📦 Test Case 3: Deleting cache item")
    event_delete = {
        "operation": "delete",
        "key": "test_key_123"
    }
    
    result_delete = lambda_handler(event_delete, None)
    print(f"Status Code: {result_delete['statusCode']}")
    
    if result_delete['statusCode'] == 200:
        print(f"✅ Delete operation successful!")
    elif result_delete['statusCode'] == 503:
        print(f"⚠️  DynamoDB table not found (expected in local testing)")
    else:
        print(f"❌ Delete operation failed: {result_delete.get('body', {})}")
    
    # Test case 4: Invalid operation
    print("\n📦 Test Case 4: Invalid operation")
    event_invalid = {
        "operation": "invalid_op",
        "key": "test_key"
    }
    
    result_invalid = lambda_handler(event_invalid, None)
    print(f"Status Code: {result_invalid['statusCode']}")
    
    if result_invalid['statusCode'] == 400:
        print(f"✅ Validation error handling works!")
    else:
        print(f"❌ Expected 400, got {result_invalid['statusCode']}")
    
    # Test case 5: Missing fields
    print("\n📦 Test Case 5: Missing required fields")
    event_missing = {
        "operation": "get"
        # Missing 'key'
    }
    
    result_missing = lambda_handler(event_missing, None)
    print(f"Status Code: {result_missing['statusCode']}")
    
    if result_missing['statusCode'] == 400:
        print(f"✅ Missing field validation works!")
    else:
        print(f"❌ Expected 400, got {result_missing['statusCode']}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
    print("\n💡 Tip: For full testing, use DynamoDB Local or mock boto3")
    print("   See README.md for setup instructions")


if __name__ == "__main__":
    test_cache_service()

