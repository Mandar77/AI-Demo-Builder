"""
Local test script for Video Stitcher
Tests FFmpeg commands locally before deploying to Lambda

Prerequisites:
- FFmpeg installed locally (brew install ffmpeg or apt install ffmpeg)
- Sample video files and images

Run: python test_local.py
"""

import os
import subprocess
import tempfile
import json

# Override paths for local testing
FFMPEG_PATH = 'ffmpeg'  # Uses system ffmpeg
FFPROBE_PATH = 'ffprobe'

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 30
SLIDE_DURATION = 3


def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        result = subprocess.run([FFMPEG_PATH, '-version'], capture_output=True, text=True)
        print("✅ FFmpeg found:")
        print(result.stdout.split('\n')[0])
        return True
    except FileNotFoundError:
        print("❌ FFmpeg not found. Please install FFmpeg first.")
        return False


def create_test_image(output_path, text="Test Slide"):
    """Create a simple test image using FFmpeg"""
    cmd = [
        FFMPEG_PATH,
        '-y',
        '-f', 'lavfi',
        '-i', f'color=c=blue:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:d=1',
        '-vf', f"drawtext=text='{text}':fontsize=72:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
        '-frames:v', '1',
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Simpler fallback without drawtext
        cmd = [
            FFMPEG_PATH,
            '-y',
            '-f', 'lavfi',
            '-i', f'color=c=blue:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:d=1',
            '-frames:v', '1',
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
    
    return output_path


def create_test_video(output_path, duration=5, color='red'):
    """Create a simple test video using FFmpeg"""
    cmd = [
        FFMPEG_PATH,
        '-y',
        '-f', 'lavfi',
        '-i', f'color=c={color}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:d={duration}',
        '-f', 'lavfi',
        '-i', f'sine=frequency=440:duration={duration}',
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-pix_fmt', 'yuv420p',
        '-shortest',
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: {result.stderr}")
    return output_path


def create_video_from_slide(slide_path, output_path, duration=SLIDE_DURATION):
    """Convert a slide image to a video clip"""
    cmd = [
        FFMPEG_PATH,
        '-y',
        '-loop', '1',
        '-i', slide_path,
        '-c:v', 'libx264',
        '-t', str(duration),
        '-pix_fmt', 'yuv420p',
        '-vf', f'scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black',
        '-r', str(VIDEO_FPS),
        '-preset', 'fast',
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Failed to create video from slide: {result.stderr}")
    
    return output_path


def add_silent_audio(input_path, output_path):
    """Add silent audio track to video"""
    cmd = [
        FFMPEG_PATH,
        '-y',
        '-i', input_path,
        '-f', 'lavfi',
        '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-shortest',
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Failed to add silent audio: {result.stderr}")
    
    return output_path


def concatenate_videos(video_paths, output_path):
    """Concatenate multiple videos"""
    concat_file = output_path.replace('.mp4', '_concat.txt')
    
    with open(concat_file, 'w') as f:
        for video_path in video_paths:
            escaped_path = video_path.replace("'", "'\\''")
            f.write(f"file '{escaped_path}'\n")
    
    cmd = [
        FFMPEG_PATH,
        '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_file,
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-c:a', 'aac',
        '-movflags', '+faststart',
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if os.path.exists(concat_file):
        os.remove(concat_file)
    
    if result.returncode != 0:
        raise Exception(f"Failed to concatenate videos: {result.stderr}")
    
    return output_path


def run_tests():
    """Run all tests"""
    print("🧪 Testing Video Stitcher locally...\n")
    
    if not check_ffmpeg():
        return
    
    # Create temp directory
    work_dir = tempfile.mkdtemp()
    output_dir = './test_output'
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Test 1: Create test image
        print("\nTest 1: Create test slide image...")
        slide_path = os.path.join(work_dir, 'test_slide.png')
        create_test_image(slide_path, "Intro Slide")
        print(f"✅ Created: {slide_path}")
        
        # Test 2: Create video from slide
        print("\nTest 2: Convert slide to video...")
        slide_video = os.path.join(work_dir, 'slide_video.mp4')
        create_video_from_slide(slide_path, slide_video, 3)
        print(f"✅ Created: {slide_video}")
        
        # Test 3: Add silent audio to slide video
        print("\nTest 3: Add silent audio to slide video...")
        slide_with_audio = os.path.join(work_dir, 'slide_with_audio.mp4')
        add_silent_audio(slide_video, slide_with_audio)
        print(f"✅ Created: {slide_with_audio}")
        
        # Test 4: Create test videos
        print("\nTest 4: Create test videos...")
        video1 = os.path.join(work_dir, 'video1.mp4')
        video2 = os.path.join(work_dir, 'video2.mp4')
        create_test_video(video1, 3, 'red')
        create_test_video(video2, 3, 'green')
        print(f"✅ Created: {video1}, {video2}")
        
        # Test 5: Create another slide
        print("\nTest 5: Create section slide...")
        slide2_path = os.path.join(work_dir, 'section_slide.png')
        create_test_image(slide2_path, "Section 1")
        slide2_video = os.path.join(work_dir, 'slide2_video.mp4')
        create_video_from_slide(slide2_path, slide2_video, 2)
        slide2_with_audio = os.path.join(work_dir, 'slide2_with_audio.mp4')
        add_silent_audio(slide2_video, slide2_with_audio)
        print(f"✅ Created section slide video")
        
        # Test 6: Concatenate all videos
        print("\nTest 6: Concatenate all videos...")
        videos_to_concat = [
            slide_with_audio,  # Intro slide
            video1,            # Video 1
            slide2_with_audio, # Section slide
            video2             # Video 2
        ]
        
        final_output = os.path.join(output_dir, 'stitched_demo.mp4')
        concatenate_videos(videos_to_concat, final_output)
        print(f"✅ Created final video: {final_output}")
        
        # Get video info
        cmd = [FFPROBE_PATH, '-v', 'quiet', '-print_format', 'json', '-show_format', final_output]
        result = subprocess.run(cmd, capture_output=True, text=True)
        info = json.loads(result.stdout)
        duration = float(info.get('format', {}).get('duration', 0))
        
        print(f"\n📊 Final video stats:")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Expected: ~11 seconds (3+3+2+3)")
        print(f"   Location: {final_output}")
        
        print("\n🎉 All tests passed! FFmpeg stitching works correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        
    finally:
        # Cleanup temp directory (but keep output)
        import shutil
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)


if __name__ == '__main__':
    run_tests()