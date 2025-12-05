import os
import sys
import json
import boto3
import uuid
from botocore.exceptions import ClientError
from google import genai

try:
    from dotenv import load_dotenv
except ImportError:
    print("Python dotenv module not found. Skipping import.")
    load_dotenv = None

def success_response(data, status_code=200):
    """Create success response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps(data)
    }

def error_response(message, status_code=500):
    """Create error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps({'error': message})
    }

# Initialize AWS clients
secrets_client = boto3.client('secretsmanager')
lambda_client = boto3.client('lambda')

# checking if the current running environment is AWS or Local
IS_LAMBDA = bool(os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))

def get_gemini_api_key():
    """
    Get Gemini API key from environment variables (local) or AWS Secrets Manager (production)

    Returns:
        str: API key or None if not found
    """
    api_key = os.environ.get('GEMINI_API_KEY')

    if api_key:
        print(f"[Service 4] ✅ ❌ Found API key in environment variables {api_key}")
    else:
        print(f"[Service 4] API key not found in environment variables")
    
    print(f"[Service 4] ✅ ❌❌❌ API key in environment variables {api_key}")
    
    return api_key

    # if testing locally
    if not IS_LAMBDA:
        load_dotenv()
        print(f"[Service 4] Running file on local computer. Fetched the key from .env file")
        api_key = os.environ.get('GEMINI_API_KEY')
        return api_key
    else:
        # trying to fetch the key from secret manager
        secret_name = os.environ.get('GEMINI_SECRET_NAME', 'ai-demo-builder/gemini-api-key')

        try:
            print(f"[Service 4] Fetching API key from Secrets Manager: {secret_name}")
            response = secrets_client.get_secret_value(SecretId=secret_name)

            if 'SecretString' in response:
                secret = response['SecretString']

                # trying to check if a dictionary is received
                try:
                    secret_dict = json.loads(secret)
                    api_key = secret_dict.get('GEMINI_API_KEY') or secret_dict.get('api_key')
                    if api_key:
                        print("[Service 4] ✅ Successfully retrieved API key from Secrets Manager")
                        return api_key
                
                except json.JSONDecodeError:
                    print("[Service 4] ✅ Successfully retrieved API key from Secrets Manager (plain text)")
                    return secret
            print("[Service 4] Secret found but no valid API key in response")
            return None
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                print(f"[Service 4] ❌ Secret not found: {secret_name}")
            elif error_code == 'AccessDeniedException':
                print(f"[Service 4] ❌ Access denied to secret: {secret_name}")
            else:
                print(f"[Service 4] ❌ AWS ClientError: {str(e)}")
            return None

        except Exception as e:
            print(f"[Service 4] ❌ Unexpected error fetching API key: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

# initializing the gemini client      
GEMINI_API_KEY = get_gemini_api_key()
client = None

if GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        print("[Service 4] ✅ Gemini client initialized successfully")
    except Exception as e:
        print(f"[Service 4] ❌ Failed to initialize Gemini client: {str(e)}")
else:
    print("[Service 4] ⚠️ GEMINI_API_KEY not found - will use fallback suggestions")

def invoke_service5_async(session_id, github_data, project_analysis, suggestions, project_metadata):
    """
    Asynchronously invoke Service 5 to store session in DynamoDB
    Fire-and-forget - we don't wait for response
    """
    try:
        service5_function_name = os.environ.get('SERVICE6_FUNCTION_NAME', 'service-6-session-creator')
        
        payload = {
            'session_id': session_id,
            'github_data': github_data,
            'project_analysis': project_analysis,
            'suggestions': suggestions,
            'project_metadata': project_metadata
        }
        
        print(f"[Service 4] Invoking Service 5 asynchronously: {service5_function_name}")
        
        # ASYNC invocation - fire and forget
        response = lambda_client.invoke(
            FunctionName=service5_function_name,
            InvocationType='Event',  # ASYNC - don't wait for response
            Payload=json.dumps(payload)
        )
        
        print(f"[Service 4] ✅ Service 5 invoked asynchronously (StatusCode: {response['StatusCode']})")
        
    except Exception as e:
        # Log error but don't fail the request - storage is not critical for user response
        print(f"[Service 4] ⚠️ Failed to invoke Service 5 (non-critical): {str(e)}")


def lambda_handler(event, context):
    """
    Service 4: AI Suggestions Service
    Generate video demo suggestions using Gemini AI
    """
    try:
        print("[Service 4] Starting AI Suggestions Generator")
        print(f"[Service 4] Event: {json.dumps(event)}")

        if 'body' in event:
            # API Gateway Format (Http request)
            print("[Service 4] Processing API Gateway Event")
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            print("[Service 4] Processing direct invocation")
            body = event
        
        print(f"[Service 4] Parsed body keys: {list(body.keys())}")

        if 'value' in body:
            # Frontend sent the complete response from Person 1
            data = body['value']
            cache_key = body.get('cacheKey', 'unknown')
            print(f"[Service 4] Processing cached data: {cache_key}")
        else:
            # Frontend sent just the extracted data
            data = body
            print("[Service 4] Processing direct data (no cache wrapper)")

        github_data = data.get('github_data', {})
        parsed_readme = data.get('parsed_readme', {})
        project_analysis = data.get('project_analysis', {})

        # validating inputs
        if not github_data:
            return error_response('github_data is required', 400)
        
        # Generating unique session id
        session_id = str(uuid.uuid4())[:8]
        print(f"[Service 4] Generated session_id: {session_id}")

        # Extracting project details
        project_name = github_data.get('projectName', 'Unknown Project')
        owner = github_data.get('owner', 'unknown')
        stars = github_data.get('stars', 0)
        language = github_data.get('language', 'Unknown')
        readme_content = github_data.get('readme', '')
        project_type = project_analysis.get('projectType', 'Unknown')

        print(f"[Service 4] Project: {owner}/{project_name}")
        print(f"[Service 4] Type: {project_type}, Language: {language}, Stars: {stars}")

        # Generate AI suggestions using all available data
        suggestion_data = generate_video_suggestions(
            project_name=project_name,
            readme_content=readme_content,
            project_type=project_type,
            project_analysis=project_analysis,
            parsed_readme=parsed_readme,
            github_data=github_data
        )

        print(f"[Service 4] ✅ Generated {len(suggestion_data.get('videos', []))} video suggestions")

        # TODO: Invoke Service 5 asynchronously to store in session table

        response_data =  {
            'session_id': session_id,
            'project_name': project_name,
            'owner': owner,
            'github_url': f"https://github.com/{owner}/{project_name}",
            'videos': suggestion_data.get('videos', []),
            'total_suggestions': len(suggestion_data.get('videos', [])),
            'overall_flow': suggestion_data.get('overall_flow', ''),
            'total_estimated_duration': suggestion_data.get('total_estimated_duration', ''),
            'project_specific_tips': suggestion_data.get('project_specific_tips', []),
            'project_metadata': {
                'type': project_type,
                'language': language,
                'stars': stars,
                'complexity': project_analysis.get('complexity', 'unknown')
            }
        }

        # Asynchronously invoke Service 5 to store session (fire-and-forget)
        invoke_service5_async(
            session_id=session_id,
            github_data=github_data,
            project_analysis=project_analysis,
            suggestions=suggestion_data,
            project_metadata=response_data['project_metadata']
        )

        return success_response(response_data)

    
    except Exception as e:
        print(f"[Service 4] ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(str(e))
    

def generate_video_suggestions(project_name, readme_content, project_type, project_analysis, parsed_readme, github_data):
    """
    Use Gemini API to generate video demo suggestions
    """
    try:
        if not client:
            print("[Service 4] ⚠️ Gemini client not initialized, using fallback")
            return create_fallback_suggestions(project_name, project_type)
        
        # Create prompt for Gemini with enhanced data
        prompt = create_gemini_prompt(
            project_name=project_name,
            readme_content=readme_content,
            project_type=project_type,
            project_analysis=project_analysis,
            parsed_readme=parsed_readme,
            github_data=github_data
        )

        print("[Service 4] Calling Gemini API...")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        print("[Service 4] ✅ Received response from Gemini")

        # Parse the response
        suggestions = parse_gemini_response(response.text)
        return suggestions
    
    except Exception as e:
        print(f"[Service 4] ❌ Gemini API Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_fallback_suggestions(project_name, project_type)
    

def create_gemini_prompt(project_name, readme_content, project_type, 
                         project_analysis, parsed_readme, github_data):
    """Create adaptive prompt that works for ANY project type"""
    max_readme_length = 3000
    if len(readme_content) > max_readme_length:
        readme_content = readme_content[:max_readme_length] + "..."

    tech_stack = project_analysis.get('techStack', [])
    key_features = project_analysis.get('keyFeatures', [])
    suggested_segments = project_analysis.get('suggestedSegments', 3)
    complexity = project_analysis.get('complexity', 'medium')
    features = parsed_readme.get('features', [])
    owner = github_data.get('owner', 'unknown')
    stars = github_data.get('stars', 0)
    language = github_data.get('language', 'Unknown')
    description = github_data.get('description', '')

    tech_stack_str = ', '.join(tech_stack) if tech_stack else 'Not Specified'
    key_features_str = '\n- '.join(key_features) if key_features else 'Not Specified'
    features_str = '\n- '.join(features) if features else 'Not Specified'

    prompt = f"""You are an expert at creating detailed video demo scripts for GitHub projects of ANY type.

PROJECT INFORMATION:
- Name: {project_name}
- Owner: {owner}
- Stars: {stars:,}
- Language: {language}
- Type: {project_type}
- Complexity: {complexity}
- Description: {description}

TECHNICAL DETAILS:
- Tech Stack: {tech_stack_str}
- Key Features: 
{key_features_str}

PARSED README FEATURES:
{features_str}

README CONTENT:
{readme_content}

IMPORTANT: Analyze the project type and adapt your suggestions accordingly:

**For WEB APPLICATIONS:** Focus on UI interactions, user flows, feature demonstrations
**For LIBRARIES/FRAMEWORKS:** Focus on code examples, API usage, integration steps
**For CLI TOOLS:** Focus on terminal commands, output examples, use cases
**For MACHINE LEARNING MODELS:** Focus on running inference, showing results, explaining model behavior
**For MOBILE APPS:** Focus on app screens, gestures, feature walkthroughs
**For DATA PROJECTS:** Focus on data loading, transformations, visualizations
**For BACKEND APIs:** Focus on endpoint testing, request/response examples, Postman/cURL demos
**For DESKTOP APPS:** Focus on UI features, workflows, settings

TASK:
Create {min(3, suggested_segments)} video suggestions that will be recorded by a user and merged together into a final demo video.

For EACH video, provide SPECIFIC, ACTIONABLE recording instructions adapted to this project's type.

EXAMPLES OF GOOD "what_to_record" INSTRUCTIONS:

**Web App Example:**
- "Navigate to localhost:3000/login"
- "Enter email: demo@example.com and password: demo123"
- "Click the Login button"
- "Show the dashboard loading with user data"

**CLI Tool Example:**
- "Open terminal in project directory"
- "Run: python tool.py --input data.csv --output results.json"
- "Show the processing output in real-time"
- "Cat the results.json file to show the output"

**ML Model Example:**
- "Open Jupyter notebook or Python script"
- "Load the pre-trained model: model = load_model('model.h5')"
- "Load sample image: img = load_image('cat.jpg')"
- "Run prediction: result = model.predict(img)"
- "Show the prediction output with confidence scores"

**Mobile App Example:**
- "Launch the app on iPhone simulator/Android emulator"
- "Tap on the + button in bottom right"
- "Fill in the form fields with sample data"
- "Swipe left to see the saved item in the list"

For each video, provide:
{{
    "videos": [
        {{
            "sequence_number": 1,
            "title": "string - Clear title indicating what will be shown",
            "duration": "string - e.g., '1.5 minutes'",
            "video_type": "string - installation|feature_demo|code_example|use_case|advanced_feature",
            "what_to_record": [
                "Step 1: Exact action to perform",
                "Step 2: Next action",
                "Step 3: What to show/highlight",
                "etc..."
            ],
            "narration_script": "string - What to say during recording (optional voiceover)",
            "key_highlights": [
                "Important feature/concept to emphasize",
                "Another highlight"
            ],
            "technical_setup": {{
                "prerequisites": ["Software needed", "Accounts required", "Data to prepare"],
                "environment": "Description of environment (browser, terminal, IDE, etc.)",
                "sample_data": "Any sample data/inputs needed"
            }},
            "expected_outcome": "What the viewer should see by the end of this video",
            "transition_to_next": "How this connects to next video"
        }}
    ],
    "overall_flow": "Brief description of the complete story these videos tell",
    "total_estimated_duration": "X minutes",
    "project_specific_tips": [
        "Recording tip specific to this type of project",
        "Another relevant tip"
    ]
}}

CRITICAL INSTRUCTIONS:
1. **Adapt to project type** - Don't give web app instructions for a CLI tool!
2. **Be ultra-specific** - Every command, every URL, every click should be spelled out
3. **Think chronologically** - Video 1 should set up context, later videos build on it
4. **Consider the viewer** - They might be seeing this project for the first time
5. **Make it filmable** - Every instruction should be something that can be screen-recorded
6. **Include actual values** - Use realistic example data, URLs, commands
7. **Logical progression** - Each video should naturally lead to the next

Return ONLY valid JSON, nothing else."""
    
    return prompt


def parse_gemini_response(response_text):
    """
    Parse Gemini's response and extract video suggestions
    """
    try:
        # Clean up the response (remove markdown code blocks if present)
        response_text = response_text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Parse JSON
        data = json.loads(response_text)
        
        # Extract all relevant fields
        videos = data.get('videos', [])
        overall_flow = data.get('overall_flow', '')
        total_duration = data.get('total_estimated_duration', '')
        recording_tips = data.get('project_specific_tips', [])
        
        print(f"[Service 4] Parsed {len(videos)} video suggestions from Gemini")
        
        # Return complete response
        return {
            'videos': videos,
            'overall_flow': overall_flow,
            'total_estimated_duration': total_duration,
            'project_specific_tips': recording_tips
        }
        
    except json.JSONDecodeError as e:
        print(f"[Service 4] ⚠️ Failed to parse Gemini response as JSON: {str(e)}")
        print(f"[Service 4] Raw response: {response_text[:500]}...")
        
        return {
            'videos': extract_suggestions_from_text(response_text),
            'overall_flow': '',
            'total_estimated_duration': '',
            'project_specific_tips': []
        }


def extract_suggestions_from_text(text):
    """
    Fallback: Try to extract video ideas from plain text response
    """
    suggestions = []
    lines = text.split('\n')
    current_suggestion = None
    
    for line in lines:
        line = line.strip()
        if line.startswith(('1.', '2.', '3.', '-', '*')) and len(line) > 10:
            if current_suggestion:
                suggestions.append(current_suggestion)
            
            current_suggestion = {
                'sequence_number': len(suggestions) + 1,
                'title': line.split('.', 1)[-1].strip().strip('-*').strip(),
                'duration': '1-2 minutes',
                'video_type': 'feature_demo',
                'what_to_record': [line.split('.', 1)[-1].strip().strip('-*').strip()],
                'narration_script': '',
                'key_highlights': [],
                'technical_setup': {
                    'prerequisites': [],
                    'environment': 'General',
                    'sample_data': ''
                },
                'expected_outcome': '',
                'transition_to_next': ''
            }
    
    if current_suggestion:
        suggestions.append(current_suggestion)
    
    if not suggestions:
        return create_fallback_suggestions("Project", "Unknown")
    
    return suggestions


def create_fallback_suggestions(project_name, project_type):
    """Create generic fallback suggestions if Gemini fails"""
    return {
        'videos': [
            {
                'sequence_number': 1,
                'title': f'Introduction to {project_name}',
                'duration': '2 minutes',
                'video_type': 'installation',
                'what_to_record': [
                    f'Show the {project_name} GitHub repository page',
                    'Navigate to the README section',
                    'Highlight the key features mentioned',
                    'Show the installation instructions'
                ],
                'narration_script': f'Welcome to {project_name}. Let\'s start by understanding what this project does and how to get it set up.',
                'key_highlights': ['Project overview', 'Main features', 'Getting started'],
                'technical_setup': {
                    'prerequisites': ['Web browser', 'GitHub account (optional)'],
                    'environment': 'GitHub website',
                    'sample_data': 'None required'
                },
                'expected_outcome': 'Viewers understand what the project does and basic setup',
                'transition_to_next': 'Now that we know what it is, let\'s see it in action...'
            },
            {
                'sequence_number': 2,
                'title': f'Exploring {project_name} Features',
                'duration': '1.5 minutes',
                'video_type': 'feature_demo',
                'what_to_record': [
                    'Open the project in a code editor or terminal',
                    'Show the project structure and main files',
                    'Demonstrate a basic use case or example',
                    'Highlight the key functionality'
                ],
                'narration_script': f'Let\'s dive into {project_name} and see how to actually use it. We\'ll walk through a simple example.',
                'key_highlights': ['Architecture', 'Key components', 'Practical use'],
                'technical_setup': {
                    'prerequisites': ['Project installed/cloned', 'Code editor or terminal'],
                    'environment': 'Local development environment',
                    'sample_data': 'Basic example from documentation'
                },
                'expected_outcome': 'Viewers can follow along and run a basic example',
                'transition_to_next': ''
            }
        ],
        'overall_flow': 'Introduction to the project followed by practical demonstration',
        'total_estimated_duration': '3.5 minutes',
        'project_specific_tips': [
            'Keep the demo focused on the most important features',
            'Use real examples rather than hypothetical scenarios',
            'Speak clearly and at a moderate pace'
        ]
    }