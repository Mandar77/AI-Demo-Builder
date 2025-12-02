#!/usr/bin/env python3
"""
测试脚本：通过 AWS Lambda Invoke 调用所有服务
不需要 API Gateway，直接使用 boto3 调用 Lambda 函数
"""

import boto3
import json
from typing import Dict, Any

# 配置 AWS 区域和 profile
REGION = 'us-west-1'
PROFILE = 'public'  # 使用我们配置的 public profile

# 创建 Lambda 客户端
session = boto3.Session(profile_name=PROFILE)
lambda_client = session.client('lambda', region_name=REGION)


def invoke_service(function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """调用 Lambda 函数"""
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    result = json.loads(response['Payload'].read())
    return result


def test_service1():
    """测试 Service 1: GitHub Fetcher"""
    print("=" * 60)
    print("测试 Service 1: GitHub Fetcher")
    print("=" * 60)
    
    payload = {
        "github_url": "https://github.com/facebook/react"
    }
    
    result = invoke_service('service1-github-fetcher', payload)
    
    if result['statusCode'] == 200:
        body = result['body']
        print(f"✅ 成功!")
        print(f"   项目: {body.get('projectName')}")
        print(f"   Stars: {body.get('stars')}")
        print(f"   Language: {body.get('language')}")
        return body
    else:
        print(f"❌ 失败: {result.get('body', {})}")
        return None


def test_service2(readme: str):
    """测试 Service 2: README Parser"""
    print("\n" + "=" * 60)
    print("测试 Service 2: README Parser")
    print("=" * 60)
    
    payload = {
        "readme": readme
    }
    
    result = invoke_service('service2-readme-parser', payload)
    
    if result['statusCode'] == 200:
        body = result['body']
        print(f"✅ 成功!")
        print(f"   标题: {body.get('title', 'N/A')[:50]}...")
        print(f"   特性数量: {len(body.get('features', []))}")
        print(f"   有文档: {body.get('hasDocumentation')}")
        return body
    else:
        print(f"❌ 失败: {result.get('body', {})}")
        return None


def test_service3(github_data: Dict, parsed_readme: Dict):
    """测试 Service 3: Project Analyzer"""
    print("\n" + "=" * 60)
    print("测试 Service 3: Project Analyzer")
    print("=" * 60)
    
    payload = {
        "github_data": github_data,
        "parsed_readme": parsed_readme
    }
    
    result = invoke_service('service3-project-analyzer', payload)
    
    if result['statusCode'] == 200:
        body = result['body']
        print(f"✅ 成功!")
        print(f"   项目类型: {body.get('projectType')}")
        print(f"   复杂度: {body.get('complexity')}")
        print(f"   技术栈: {', '.join(body.get('techStack', []))}")
        print(f"   建议分段数: {body.get('suggestedSegments')}")
        return body
    else:
        print(f"❌ 失败: {result.get('body', {})}")
        return None


def test_service4():
    """测试 Service 4: Cache Service"""
    print("\n" + "=" * 60)
    print("测试 Service 4: Cache Service")
    print("=" * 60)
    
    # Test Set
    print("\n1. 测试 Set 操作...")
    payload_set = {
        "operation": "set",
        "key": "test_integration_key",
        "value": {"test": "data", "number": 123},
        "ttl": 3600
    }
    result_set = invoke_service('service4-cache-service', payload_set)
    if result_set['statusCode'] == 200:
        print(f"   ✅ Set 成功: {result_set['body']}")
    else:
        print(f"   ❌ Set 失败: {result_set.get('body', {})}")
        return
    
    # Test Get
    print("\n2. 测试 Get 操作...")
    payload_get = {
        "operation": "get",
        "key": "test_integration_key"
    }
    result_get = invoke_service('service4-cache-service', payload_get)
    if result_get['statusCode'] == 200:
        body = result_get['body']
        if body.get('found'):
            print(f"   ✅ Get 成功: 找到缓存")
            print(f"   值: {body.get('value')}")
        else:
            print(f"   ⚠️  缓存未找到")
    else:
        print(f"   ❌ Get 失败: {result_get.get('body', {})}")
    
    # Test Delete
    print("\n3. 测试 Delete 操作...")
    payload_delete = {
        "operation": "delete",
        "key": "test_integration_key"
    }
    result_delete = invoke_service('service4-cache-service', payload_delete)
    if result_delete['statusCode'] == 200:
        print(f"   ✅ Delete 成功: {result_delete['body']}")
    else:
        print(f"   ❌ Delete 失败: {result_delete.get('body', {})}")


def test_integration():
    """完整集成测试"""
    print("\n" + "=" * 60)
    print("完整集成测试")
    print("=" * 60)
    
    # Step 1: Service 1
    github_data = test_service1()
    if not github_data:
        return
    
    # Step 2: Service 2
    readme = github_data.get('readme', '')
    parsed_readme = test_service2(readme)
    if not parsed_readme:
        return
    
    # Step 3: Service 3
    github_data_for_service3 = {k: v for k, v in github_data.items() if k != 'readme'}
    analysis = test_service3(github_data_for_service3, parsed_readme)
    
    # Step 4: Service 4
    test_service4()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_integration()
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        print("\n请确保：")
        print("1. 已安装 boto3: pip3 install boto3")
        print("2. AWS 凭证已正确配置")
        print("3. 所有 Lambda 函数已部署")

