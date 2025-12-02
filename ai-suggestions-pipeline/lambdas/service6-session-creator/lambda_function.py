import os
import sys
import json
import uuid
import requests
import boto3
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../shared'))
from constants import Status, GITHUB_REPO_ANALYSIS_API_URL, GITHUB_REPO_ANALYSIS_API_TIMEOUT
from response_utils import success_response, error_response

lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    """Service 6: Session Creator & Orchestrator"""
    try:
        print(f"[Service 6] Starting Orchestrator")

        # parse input - getting the github url from the frontend request
        body = json.loads(event.get('body', '{}')) if event.get('body') else event
        repo_url = body.get('repo_url') or body.get('github_url')

        if not repo_url:
            return error_response('repo_url or github_url is required', 400)
        
        if not repo_url.startswith('http'):
            repo_url = f'https://{repo_url}'

        # Generating Session ID
        session_id = str(uuid.uuid4())[:8]
        print(f"[Service 6] Created session: {session_id}")

        # Call Person 1's API - Github Analysis
        print(f"[Service 6] Calling Person 1's API: {GITHUB_REPO_ANALYSIS_API_URL}")
        github_analysis_response = call_github_analysis_api(repo_url)

        if not github_analysis_response:
            return error_response('Failed to analyze repository', 500)
        
        print(f"[Service 6] ✅ Got analysis from Person 1")
        print(f"[Service 6] Project: {github_analysis_response['github_data']['projectName']}")
        print(f"[Service 6] Type: {github_analysis_response['project_analysis']['projectType']}")
        print(f"[Service 6] response from analysis API: {github_analysis_response}")

        # Step 2: Call Service 4 to generate AI suggestions
        print(f"[Service 6] Calling Service 4 for AI Suggestions")
        suggestions = call_service4(session_id, github_analysis_response)

        print(f"[Service 6] ✅ Generated {len(suggestions.get('videos', []))} suggestions")

        #TODO : store the respnse in dyamodb table

        return success_response({
            'session_id': session_id,
            "repo_url": repo_url,
            "project_name": github_analysis_response['github_data']['projectName'],
            "suggestions": suggestions,
            "status": Status.INITIALIZED
        })
    
    except Exception as e:
        print(f"[Service 6] ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(str(e))


def call_github_analysis_api(repo_url):
    """
    Call Github Analysis API

    Args:
        repo_url: Github Repository URL

    Returns:
        Analysis response from the API
    """
    try:
        response = requests.post(
            GITHUB_REPO_ANALYSIS_API_URL,
            json={'github_url' : repo_url},
            timeout=GITHUB_REPO_ANALYSIS_API_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.Timeout:
        print(f"[Service 6] ⏱️ Timeout calling Person 1's API")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[Service 6] ❌ Error calling Person 1's API: {str(e)}")
        return None
    
def call_service4(session_id, github_analysis_response):
    return None







