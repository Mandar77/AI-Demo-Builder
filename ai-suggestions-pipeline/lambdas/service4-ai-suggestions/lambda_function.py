import os
import sys
import json
import boto3
import uuid
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from google import genai

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../shared'))
from response_utils import success_response, error_response

# Initialize AWS clients
secrets_client = boto3.client('secretsmanager')

# checking if the current running enviornment is AWS or Local
IS_LAMBDA = bool(os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))

def get_gemini_api_key():
    """
    Get Gemini API key from environment variables (local) or AWS Secrets Manager (production)

    Returns:
        str: API key or None if not found
    """
    api_key = None
    is_lambda = bool(os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))

    # if testing locally
    if not is_lambda:
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
            # Convert to dict/json object it is string else keep as it is
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
        project_type = project_analysis.get('projecType', 'Unknow')

        print(f"[Service 4] Project: {owner}/{project_name}")
        print(f"[Service 4] Type: {project_type}, Language: {language}, Stars: {stars}")

        # Generate AI suggestions using all available data
        suggestions = generate_video_suggestions(
            project_name=project_name,
            readme_content=readme_content,
            project_type=project_type,
            project_analysis=project_analysis,
            parsed_readme=parsed_readme,
            github_data=github_data
        )

        print(f"[Service 4] ✅ Generated {len(suggestions)} video suggestions")

        # TODO: Store in the session table


        return success_response({
            'session_id': session_id,
            'project_name': project_name,
            'owner': owner,
            'github_url': f"https://github.com/{owner}/{project_name}",
            'videos': suggestions,
            'total_suggestions': len(suggestions),
            'project_metadata': {
                'type' : project_type,
                'language' : language,
                'stars' : stars,
                'complexity' : project_analysis.get('complexity', 'unknown')
            }
        })
    
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
            model = "gemini-2.0-flash-exp",
            contents = prompt
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
    

def create_gemini_prompt(project_name, readme_content, project_type, project_analysis, parsed_readme, github_data):
    """
    Create a detailed prompt for Gemini to generate video suggestions
    """

    # Truncate README if too long
    max_readme_length = 3000
    if len(readme_content) > max_readme_length:
        readme_content = readme_content[:max_readme_length] + "..."

    # Extract useful informtion
    tech_stack = project_analysis.get('techStack', [])
    key_features = project_analysis.get('keyFeatures', [])
    suggested_segments = project_analysis.get('suggestedSegments', 3)
    complexity = project_analysis.get('complexity', 'medium')

    features = parsed_readme.get('features', [])
    has_documentation = parsed_readme.get('hasDocumentation', False)

    owner = github_data.get('owner', 'unknown')
    stars = github_data.get('stars', 0)
    language = github_data.get('language', 'Unknown')
    description = github_data.get('description', '')

    tech_stack_str = ' '.join(tech_stack) if tech_stack else 'Not Specified'
    key_features_str = '\n- '.join(key_features) if key_features else 'Not Specified'
    features_str = '\n- '.join(features) if features else 'Not Specified'

    prompt = f"""You are expert at creation engaging demo video suggestions for Github projects.

    PROJECT INFORMATION:
    - Name: {project_name}
    - Owner: {owner}
    - Github Stars: {stars:,}
    - Primary Language: {language}
    - Project Type: {project_type}
    - Complexity: {complexity}
    - Description: {description}

    TECHNICAL DETAILS:
    - Tech Stack: {tech_stack_str}
    - Key Features: {key_features_str}

    PARSED README FEATURES:
    {features_str}

    README CONTENT:
    {readme_content}

    TASK:
    Generate {min(3, suggested_segments)} short demo video suggestions (1-2 minutes each) that would effectively showcase this project to potential users and developers. Also, tell the sequence of the suggestions, example which suggestion should be completed first, followed by which, and so on

    Consider:
    1. The project's complexity level ({complexity})
    2. The target audience (based on stars: {stars:,} and tech stack)
    3. Key features that should be highlighted
    4. Whether documentation is available: {has_documentation}

    For each video suggestion, provide:
    1. title: A catchy, descriptive title
    2. duration: Estimated duration (e.g., "1.5 minutes", "2 minutes")
    3. description: Brief description of what the video covers
    4. key_points: List of 3-4 main points to demonstrate
    5. target_audience: Who would benefit from this video (e.g., "Beginners", "Developers", "Technical Users")
    6. hook: An attention-grabbing opening line for the video
    7. script_outline: A brief 3-4 step outline of the video flow

    Return ONLY valid JSON in this exact format (no markdown, no extra text):
    {{
        "videos" : [
         {{
            "title": "string",
            "duration":"string",
            "description":"string",
            "key_points":["point1", "point2", "point3"],
            "target_audience":"string",
            "hook":"string",
            "script_outline" : ["step1", "step2", "step3"]
         }}
        ]
    }}

    IMPORTANT: Return only the JSON object, nothing else"""

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
        videos = data.get('videos', [])
        
        print(f"[Service 4] Parsed {len(videos)} video suggestions from Gemini")
        
        return videos
        
    except json.JSONDecodeError as e:
        print(f"[Service 4] ⚠️ Failed to parse Gemini response as JSON: {str(e)}")
        print(f"[Service 4] Raw response: {response_text[:500]}...")
        
        return extract_suggestions_from_text(response_text)


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
                'title': line.split('.', 1)[-1].strip().strip('-*').strip(),
                'duration': '1-2 minutes',
                'description': line.split('.', 1)[-1].strip().strip('-*').strip(),
                'key_points': [],
                'target_audience': 'General',
                'hook': 'Let me show you something interesting',
                'script_outline': []
            }
    
    if current_suggestion:
        suggestions.append(current_suggestion)
    
    return suggestions if suggestions else create_fallback_suggestions("Project", "Unknown")


def create_fallback_suggestions(project_name, project_type):
    """
    Create generic fallback suggestions if Gemini fails
    """
    return [
        {
            'title': f'Introduction to {project_name}',
            'duration': '2 minutes',
            'description': f'A quick overview of the {project_name} project and its key features',
            'key_points': [
                'Project overview',
                'Main features',
                'Getting started'
            ],
            'target_audience': 'Beginners',
            'hook': f'Discover what makes {project_name} special',
            'script_outline': [
                'Introduction',
                'Feature demonstration',
                'Quick start guide'
            ]
        },
        {
            'title': f'Deep Dive into {project_name}',
            'duration': '1.5 minutes',
            'description': f'Exploring the technical aspects of {project_name}',
            'key_points': [
                'Architecture overview',
                'Key components',
                'Use cases'
            ],
            'target_audience': 'Developers',
            'hook': f'Let\'s explore how {project_name} works under the hood',
            'script_outline': [
                'System architecture',
                'Code walkthrough',
                'Practical examples'
            ]
        }
    ]