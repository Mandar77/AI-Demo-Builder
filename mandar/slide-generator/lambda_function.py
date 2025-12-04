"""
Slide Generator Service (Service 12) - Pillow Version
Creates PNG transition slides with text using PIL/Pillow
No Lambda layers required!
"""

import os
import json
import boto3
from datetime import datetime
import tempfile
import shutil
from PIL import Image, ImageDraw, ImageFont

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Configuration
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'cs6620-ai-builder-project')
TABLE_NAME = os.environ.get('TABLE_NAME', 'ai-demo-sessions')
PARTITION_KEY = os.environ.get('PARTITION_KEY', 'project_name')

# Slide dimensions
SLIDE_WIDTH = 1920
SLIDE_HEIGHT = 1080

# Color schemes for different slide types (RGB tuples)
COLOR_SCHEMES = {
    'title': {
        'bg_color': (26, 26, 46),       # Dark blue #1a1a2e
        'title_color': (255, 255, 255),  # White
        'subtitle_color': (160, 160, 160), # Gray
        'accent_color': (79, 70, 229)    # Purple #4f46e5
    },
    'section': {
        'bg_color': (15, 23, 42),        # Darker blue #0f172a
        'title_color': (255, 255, 255),
        'subtitle_color': (203, 213, 225), # #cbd5e1
        'accent_color': (59, 130, 246)   # Blue #3b82f6
    },
    'end': {
        'bg_color': (30, 27, 75),        # Indigo #1e1b4b
        'title_color': (255, 255, 255),
        'subtitle_color': (196, 181, 253), # #c4b5fd
        'accent_color': (139, 92, 246)   # Violet #8b5cf6
    }
}


def get_font(size):
    """Get a font, falling back to default if custom fonts unavailable"""
    # Try different font paths (Lambda has limited fonts)
    font_paths = [
        '/usr/share/fonts/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/var/task/fonts/DejaVuSans.ttf',
        '/usr/share/fonts/liberation/LiberationSans-Regular.ttf',
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
    
    # Fall back to default font (smaller, but works)
    try:
        return ImageFont.load_default()
    except:
        return None


def get_text_size(draw, text, font):
    """Get text bounding box size"""
    if font:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    return len(text) * 10, 20  # Rough estimate for default font


def draw_centered_text(draw, text, y_position, font, color, width=SLIDE_WIDTH):
    """Draw text centered horizontally at given y position"""
    if not text:
        return
    
    text_width, text_height = get_text_size(draw, text, font)
    x = (width - text_width) // 2
    draw.text((x, y_position), text, font=font, fill=color)


def update_session_status(project_name, status, additional_data=None):
    """Update session status in DynamoDB"""
    table = dynamodb.Table(TABLE_NAME)
    now = datetime.utcnow().isoformat()
    
    update_expr = 'SET #status = :status, updated_at = :now'
    expr_names = {'#status': 'status'}
    expr_values = {':status': status, ':now': now}
    
    if additional_data:
        for key, value in additional_data.items():
            safe_key = key.replace('-', '_')
            update_expr += f', #{safe_key} = :{safe_key}'
            expr_names[f'#{safe_key}'] = key
            # Convert non-serializable types
            if isinstance(value, (list, dict)):
                expr_values[f':{safe_key}'] = value
            else:
                expr_values[f':{safe_key}'] = str(value) if not isinstance(value, (str, int, float, bool)) else value
    
    try:
        table.update_item(
            Key={PARTITION_KEY: project_name},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values
        )
        print(f"Updated status to '{status}' for project: {project_name}")
    except Exception as e:
        print(f"Warning: Could not update DynamoDB: {e}")


def add_gradient_overlay(img, scheme):
    """Add a subtle gradient overlay to make slides more visually appealing"""
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Create vertical gradient (darker at bottom)
    for y in range(SLIDE_HEIGHT):
        alpha = int((y / SLIDE_HEIGHT) * 30)  # Subtle gradient
        draw.line([(0, y), (SLIDE_WIDTH, y)], fill=(0, 0, 0, alpha))
    
    # Composite the gradient onto the image
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, overlay)
    return img.convert('RGB')


def create_title_slide(content, scheme):
    """Create a title slide"""
    img = Image.new('RGB', (SLIDE_WIDTH, SLIDE_HEIGHT), scheme['bg_color'])
    draw = ImageDraw.Draw(img)
    
    # Add gradient overlay
    img = add_gradient_overlay(img, scheme)
    draw = ImageDraw.Draw(img)
    
    title = content.get('title', 'Demo')
    subtitle = content.get('subtitle', '')
    project_name = content.get('projectName', '')
    
    # Fonts
    title_font = get_font(96)
    subtitle_font = get_font(48)
    project_font = get_font(32)
    
    # Calculate vertical positions
    center_y = SLIDE_HEIGHT // 2
    
    # Draw title (centered)
    draw_centered_text(draw, title, center_y - 100, title_font, scheme['title_color'])
    
    # Draw subtitle
    if subtitle:
        draw_centered_text(draw, subtitle, center_y + 20, subtitle_font, scheme['subtitle_color'])
    
    # Draw project name at bottom
    if project_name:
        draw_centered_text(draw, project_name, SLIDE_HEIGHT - 120, project_font, scheme['accent_color'])
    
    # Add decorative line under title
    line_y = center_y - 10
    line_width = 200
    line_x = (SLIDE_WIDTH - line_width) // 2
    draw.rectangle([line_x, line_y, line_x + line_width, line_y + 4], fill=scheme['accent_color'])
    
    return img


def create_section_slide(content, scheme):
    """Create a section slide"""
    img = Image.new('RGB', (SLIDE_WIDTH, SLIDE_HEIGHT), scheme['bg_color'])
    draw = ImageDraw.Draw(img)
    
    # Add gradient overlay
    img = add_gradient_overlay(img, scheme)
    draw = ImageDraw.Draw(img)
    
    section_num = content.get('sectionNumber', '')
    section_title = content.get('sectionTitle', 'Section')
    section_desc = content.get('sectionDescription', '')
    
    # Fonts
    num_font = get_font(36)
    title_font = get_font(72)
    desc_font = get_font(36)
    
    center_y = SLIDE_HEIGHT // 2
    
    # Draw section number
    if section_num:
        section_label = f"Section {section_num}"
        draw_centered_text(draw, section_label, center_y - 140, num_font, scheme['accent_color'])
    
    # Draw section title
    draw_centered_text(draw, section_title, center_y - 40, title_font, scheme['title_color'])
    
    # Draw description
    if section_desc:
        draw_centered_text(draw, section_desc, center_y + 60, desc_font, scheme['subtitle_color'])
    
    # Add decorative elements
    # Left accent bar
    draw.rectangle([100, center_y - 50, 108, center_y + 50], fill=scheme['accent_color'])
    # Right accent bar
    draw.rectangle([SLIDE_WIDTH - 108, center_y - 50, SLIDE_WIDTH - 100, center_y + 50], fill=scheme['accent_color'])
    
    return img


def create_end_slide(content, scheme):
    """Create an end/thank you slide"""
    img = Image.new('RGB', (SLIDE_WIDTH, SLIDE_HEIGHT), scheme['bg_color'])
    draw = ImageDraw.Draw(img)
    
    # Add gradient overlay
    img = add_gradient_overlay(img, scheme)
    draw = ImageDraw.Draw(img)
    
    title = content.get('title', 'Thank You!')
    subtitle = content.get('subtitle', '')
    
    # Fonts
    title_font = get_font(96)
    subtitle_font = get_font(42)
    
    center_y = SLIDE_HEIGHT // 2
    
    # Draw main title
    draw_centered_text(draw, title, center_y - 60, title_font, scheme['title_color'])
    
    # Draw subtitle
    if subtitle:
        draw_centered_text(draw, subtitle, center_y + 50, subtitle_font, scheme['subtitle_color'])
    
    # Add decorative circle/ring
    circle_size = 300
    circle_x = SLIDE_WIDTH // 2
    circle_y = center_y
    for i in range(3):
        offset = i * 20
        draw.ellipse([
            circle_x - circle_size - offset,
            circle_y - circle_size - offset,
            circle_x + circle_size + offset,
            circle_y + circle_size + offset
        ], outline=(*scheme['accent_color'], 50 - i * 15), width=2)
    
    return img


def create_slide(slide_type, content):
    """Create a slide based on type"""
    scheme = COLOR_SCHEMES.get(slide_type, COLOR_SCHEMES['section'])
    
    if slide_type == 'title':
        return create_title_slide(content, scheme)
    elif slide_type == 'section':
        return create_section_slide(content, scheme)
    elif slide_type == 'end':
        return create_end_slide(content, scheme)
    else:
        # Default to section style
        return create_section_slide(content, scheme)


def upload_to_s3(local_path, s3_key):
    """Upload file to S3"""
    print(f"Uploading {local_path} to s3://{BUCKET_NAME}/{s3_key}")
    s3_client.upload_file(
        local_path,
        BUCKET_NAME,
        s3_key,
        ExtraArgs={'ContentType': 'image/png'}
    )
    return f"s3://{BUCKET_NAME}/{s3_key}"


def process_request(event):
    """Main processing logic"""
    # Parse request
    if isinstance(event.get('body'), str):
        body = json.loads(event['body'])
    elif event.get('body'):
        body = event['body']
    else:
        body = event
    
    # Support both project_name and session_id
    project_name = body.get('project_name') or body.get('session_id')
    if not project_name:
        raise ValueError('project_name is required')
    
    slides = body.get('slides', [])
    if not slides:
        raise ValueError('slides array is required')
    
    print(f"Generating {len(slides)} slides for project: {project_name}")
    
    # Update status
    update_session_status(project_name, 'generating_slides', {
        'processing_step': f'Creating {len(slides)} slides',
        'total_slides': len(slides),
        'current_slide': 0
    })
    
    # Create temp directory
    work_dir = tempfile.mkdtemp()
    
    try:
        generated_slides = []
        
        for idx, slide in enumerate(slides):
            slide_id = slide.get('id', f'slide_{idx}')
            slide_type = slide.get('type', 'section')
            content = slide.get('content', {})
            
            print(f"Creating slide {idx + 1}/{len(slides)}: {slide_id} ({slide_type})")
            
            # Update progress
            update_session_status(project_name, 'generating_slides', {
                'processing_step': f'Creating slide {idx + 1}/{len(slides)}: {slide_id}',
                'current_slide': idx + 1
            })
            
            # Create the slide image
            img = create_slide(slide_type, content)
            
            # Save locally
            local_path = os.path.join(work_dir, f'{slide_id}.png')
            img.save(local_path, 'PNG', quality=95)
            
            # Upload to S3
            s3_key = f'slides/{project_name}/{slide_id}.png'
            s3_url = upload_to_s3(local_path, s3_key)
            
            generated_slides.append({
                'id': slide_id,
                'type': slide_type,
                's3_key': s3_key,
                's3_url': s3_url,
                'order': idx
            })
            
            print(f"Created slide: {s3_key}")
        
        # Update final status
        result = {
            'project_name': project_name,
            'slides_count': len(generated_slides),
            'slides': generated_slides,
            'created_at': datetime.utcnow().isoformat()
        }
        
        update_session_status(project_name, 'slides_ready', {
            'slides': generated_slides,
            'slides_count': len(generated_slides),
            'processing_step': 'All slides generated'
        })
        
        return result
        
    finally:
        # Cleanup
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)


def lambda_handler(event, context):
    """Lambda entry point"""
    print(f"Slide Generator invoked: {json.dumps(event, indent=2)}")
    
    try:
        result = process_request(event)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'data': result
            })
        }
        
    except ValueError as e:
        print(f"Validation error: {e}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            body = event.get('body', event)
            if isinstance(body, str):
                body = json.loads(body)
            project_name = body.get('project_name') or body.get('session_id')
            if project_name:
                update_session_status(project_name, 'slides_failed', {
                    'error_message': str(e)
                })
        except:
            pass
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }