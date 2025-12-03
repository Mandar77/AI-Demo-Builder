"""
Local test script for Video Optimizer
Tests FFmpeg encoding locally before deploying to Lambda

Prerequisites:
- FFmpeg installed locally
- Sample video file (or uses test video from video-stitcher)

Run: python test_local.py
"""

import os
import subprocess
import tempfile
import json

# Override paths for local testing
FFMPEG_PATH = 'ffmpeg'
FFPROBE_PATH = 'ffprobe'

# Output presets
PRESETS = {
    '1080p': {
        'width': 1920,
        'height': 1080,
        'bitrate': '5M',
        'maxrate': '6M',
        'bufsize': '10M',
        'crf': 23,
        'audio_bitrate': '192k'
    },
    '720p': {
        'width': 1280,
        'height': 720,
        'bitrate': '2.5M',
        'maxrate': '3M',
        'bufsize': '5M',
        'crf': 24,
        'audio_bitrate': '128k'
    },
    '480p': {
        'width': 854,
        'height': 480,
        'bitrate': '1M',
        'maxrate': '1.5M',
        'bufsize': '2M',
        'crf': 25,
        'audio_bitrate': '96k'
    }
}


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


def get_video_info(video_path):
    """Get video information"""
    cmd = [
        FFPROBE_PATH,
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        video_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)
    
    format_info = info.get('format', {})
    duration = float(format_info.get('duration', 0))
    file_size = int(format_info.get('size', 0))
    
    video_stream = None
    for stream in info.get('streams', []):
        if stream['codec_type'] == 'video':
            video_stream = stream
            break
    
    return {
        'duration': duration,
        'file_size': file_size,
        'width': video_stream.get('width', 0) if video_stream else 0,
        'height': video_stream.get('height', 0) if video_stream else 0
    }


def create_test_video(output_path, duration=10):
    """Create a test video for optimization testing"""
    cmd = [
        FFMPEG_PATH,
        '-y',
        '-f', 'lavfi',
        '-i', f'testsrc=duration={duration}:size=1920x1080:rate=30',
        '-f', 'lavfi',
        '-i', f'sine=frequency=440:duration={duration}',
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-pix_fmt', 'yuv420p',
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: {result.stderr}")
    return output_path


def optimize_video(input_path, output_path, preset_name):
    """Encode video with specified preset"""
    preset = PRESETS[preset_name]
    
    cmd = [
        FFMPEG_PATH,
        '-y',
        '-i', input_path,
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', str(preset['crf']),
        '-maxrate', preset['maxrate'],
        '-bufsize', preset['bufsize'],
        '-vf', f"scale={preset['width']}:{preset['height']}:force_original_aspect_ratio=decrease,pad={preset['width']}:{preset['height']}:(ow-iw)/2:(oh-ih)/2:black",
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', preset['audio_bitrate'],
        '-ar', '44100',
        '-ac', '2',
        '-movflags', '+faststart',
        output_path
    ]
    
    print(f"  Command: ffmpeg ... -vf scale={preset['width']}:{preset['height']} ... {output_path}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    
    if result.returncode != 0:
        raise Exception(f"Encoding failed: {result.stderr}")
    
    return output_path


def generate_thumbnail(input_path, output_path):
    """Generate thumbnail from video"""
    cmd = [
        FFMPEG_PATH,
        '-y',
        '-i', input_path,
        '-ss', '00:00:01',
        '-vframes', '1',
        '-vf', 'scale=640:360:force_original_aspect_ratio=decrease,pad=640:360:(ow-iw)/2:(oh-ih)/2:black',
        '-q:v', '2',
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def format_size(size_bytes):
    """Format file size for display"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def run_tests():
    """Run all tests"""
    print("🧪 Testing Video Optimizer locally...\n")
    
    if not check_ffmpeg():
        return
    
    # Create output directory
    output_dir = './test_output'
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if we have a test video from video-stitcher
    stitched_video = os.path.join(output_dir, 'stitched_demo.mp4')
    
    work_dir = tempfile.mkdtemp()
    
    try:
        # Get or create input video
        if os.path.exists(stitched_video):
            print(f"\nUsing existing stitched video: {stitched_video}")
            input_path = stitched_video
        else:
            print("\nTest 1: Creating test input video (10 seconds)...")
            input_path = os.path.join(work_dir, 'test_input.mp4')
            create_test_video(input_path, 10)
            print(f"✅ Created: {input_path}")
        
        # Get input info
        input_info = get_video_info(input_path)
        print(f"\n📊 Input video:")
        print(f"   Resolution: {input_info['width']}x{input_info['height']}")
        print(f"   Duration: {input_info['duration']:.2f} seconds")
        print(f"   File size: {format_size(input_info['file_size'])}")
        
        # Test encoding at different resolutions
        results = []
        
        for resolution in ['1080p', '720p', '480p']:
            print(f"\nTest: Encoding {resolution}...")
            output_path = os.path.join(output_dir, f'optimized_{resolution}.mp4')
            
            optimize_video(input_path, output_path, resolution)
            
            output_info = get_video_info(output_path)
            results.append({
                'resolution': resolution,
                'path': output_path,
                'width': output_info['width'],
                'height': output_info['height'],
                'duration': output_info['duration'],
                'file_size': output_info['file_size']
            })
            
            print(f"✅ {resolution}: {output_info['width']}x{output_info['height']}, {format_size(output_info['file_size'])}")
        
        # Test thumbnail generation
        print("\nTest: Generating thumbnail...")
        thumb_path = os.path.join(output_dir, 'thumbnail.jpg')
        if generate_thumbnail(input_path, thumb_path):
            print(f"✅ Thumbnail generated: {thumb_path}")
        else:
            print("⚠️ Thumbnail generation failed")
        
        # Summary
        print("\n" + "="*60)
        print("📊 OPTIMIZATION RESULTS SUMMARY")
        print("="*60)
        print(f"{'Resolution':<12} {'Dimensions':<14} {'Size':<12} {'Compression':<12}")
        print("-"*60)
        
        for r in results:
            compression = (1 - r['file_size'] / input_info['file_size']) * 100 if input_info['file_size'] > 0 else 0
            print(f"{r['resolution']:<12} {r['width']}x{r['height']:<6} {format_size(r['file_size']):<12} {compression:.1f}% smaller")
        
        print("-"*60)
        print(f"\n📁 Output files saved to: {output_dir}/")
        print("\n🎉 All optimization tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        
    finally:
        import shutil
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)


if __name__ == '__main__':
    run_tests()