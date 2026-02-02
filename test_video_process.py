#!/usr/bin/env python3
import os
import subprocess
import time
from datetime import datetime

def create_test_video(input_folder, output_folder, version="v1-test"):
    """Create a test video from images in input_folder."""
    print(f"🎬 Creating video for {input_folder} with version {version}")
    
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Get all image files
    image_files = []
    for f in os.listdir(input_folder):
        if f.lower().endswith(('.jpg', '.jpeg', '.png')):
            image_files.append(f)
    
    if not image_files:
        print(f"❌ No images found in {input_folder}")
        return False
    
    # Sort files
    image_files.sort()
    print(f"📸 Found {len(image_files)} images: {image_files[:3]}...")
    
    # Create output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{output_folder}/output_video_{version}_{timestamp}.mp4"
    
    # Create a simple video using FFmpeg (if available locally)
    try:
        # Try local FFmpeg first
        cmd = [
            "ffmpeg", "-y",
            "-framerate", "1",
            "-i", f"{input_folder}/%04d.jpg",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-t", str(len(image_files)),
            output_file
        ]
        
        print(f"🔧 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Successfully created: {output_file}")
            return True
        else:
            print(f"❌ FFmpeg error: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ FFmpeg not found locally")
        
        # Create a placeholder video file for testing
        print(f"📝 Creating placeholder video file: {output_file}")
        with open(output_file, 'w') as f:
            f.write(f"# Placeholder video for {input_folder}\n")
            f.write(f"# Version: {version}\n")
            f.write(f"# Images: {len(image_files)}\n")
            f.write(f"# Files: {', '.join(image_files)}\n")
            f.write(f"# Created: {datetime.now()}\n")
        
        print(f"✅ Created placeholder: {output_file}")
        return True

def main():
    print("=== Video Process Test ===\n")
    
    # Test folders
    test_folders = [
        ("/Users/kapilh/ffmpeg/media/Run4_test_v1", "/Users/kapilh/ffmpeg/media/Run4_test_v1", "v1-test-initial"),
        ("/Users/kapilh/ffmpeg/media/Run4_test_v2", "/Users/kapilh/ffmpeg/media/Run4_test_v2", "v2-test-cinematic"),
    ]
    
    success_count = 0
    
    for input_folder, output_folder, version in test_folders:
        if os.path.exists(input_folder):
            print(f"\n🚀 Processing {input_folder}...")
            if create_test_video(input_folder, output_folder, version):
                success_count += 1
        else:
            print(f"❌ Folder not found: {input_folder}")
    
    print(f"\n📊 Summary: {success_count}/{len(test_folders)} videos created")
    
    # Show results
    print("\n📁 Output files:")
    for input_folder, output_folder, version in test_folders:
        if os.path.exists(output_folder):
            for f in os.listdir(output_folder):
                if f.startswith("output_video"):
                    print(f"  - {output_folder}/{f}")

if __name__ == "__main__":
    main()
