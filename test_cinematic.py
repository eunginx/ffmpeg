#!/usr/bin/env python3
import os
import subprocess
import sys
import time

def create_test_images():
    """Create test images for the cinematic video."""
    test_dir = "test_cinematic"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create 3 test images with different colors
    colors = ["red", "blue", "green"]
    texts = ["Convert any photo into beautiful hyper personalised merch!", 
             "Browse through our gallery of lovingly curated avatars",
             "Upload any photo of your choice, a selfie or wefie"]
    
    for i, (color, text) in enumerate(zip(colors, texts)):
        print(f"Creating test image {i+1}...")
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c={color}:s=1920x1080:d=3",
            "-vf", f"drawtext=text='{text}':fontsize=60:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:borderw=2:bordercolor=black",
            f"{test_dir}/{i:04d}.jpg"
        ]
        subprocess.run(cmd, check=True)
    
    return test_dir

def create_test_audio():
    """Create a test audio file."""
    test_dir = "test_cinematic"
    print("Creating test audio...")
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=440:duration=9",
        f"{test_dir}/test_audio.mp3"
    ]
    subprocess.run(cmd, check=True)
    return f"{test_dir}/test_audio.mp3"

def run_test():
    """Run the cinematic video generation test."""
    print("=== Cinematic Video Generation Test ===\n")
    
    # Create test media
    test_dir = create_test_images()
    audio_path = create_test_audio()
    
    # Create a UUID for testing
    test_uuid = "test_cinematic_uuid"
    
    # Create the test directory structure
    media_dir = "/Users/kapilh/ffmpeg/media"
    test_media_dir = os.path.join(media_dir, test_uuid)
    os.makedirs(test_media_dir, exist_ok=True)
    
    # Copy test images to media directory
    for i in range(3):
        src = f"{test_dir}/{i:04d}.jpg"
        dst = f"{test_media_dir}/{i:04d}.jpg"
        subprocess.run(["cp", src, dst], check=True)
    
    # Copy test audio
    music_dir = "/Users/kapilh/ffmpeg/music"
    os.makedirs(music_dir, exist_ok=True)
    subprocess.run(["cp", audio_path, f"{music_dir}/test_audio.mp3"], check=True)
    
    print(f"\nTest media prepared in: {test_media_dir}")
    print("Starting Docker containers...")
    
    # Start the Docker containers
    subprocess.run(["docker-compose", "up", "-d"], check=True)
    
    print("Waiting for containers to initialize...")
    time.sleep(5)
    
    print("\nMonitoring for video generation...")
    print("You should see output videos in: /Users/kapilh/ffmpeg/media/test_cinematic_uuid/")
    print("Look for files named: output_video_*_v2-cinematic.mp4")
    
    # Monitor the output directory
    max_wait = 60  # Wait up to 60 seconds
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        output_files = [f for f in os.listdir(test_media_dir) if f.startswith("output_video") and f.endswith(".mp4")]
        if output_files:
            print(f"\n✅ Success! Generated video(s):")
            for f in output_files:
                print(f"  - {f}")
            print(f"\nVideo location: {test_media_dir}")
            break
        time.sleep(2)
    
    if not output_files:
        print("\n⚠️  No videos generated within the timeout period.")
        print("Check the container logs with: docker-compose logs file_watcher_main")
    
    # Cleanup
    print("\nCleaning up test files...")
    subprocess.run(["rm", "-rf", test_dir], check=True)
    print("Test complete!")

if __name__ == "__main__":
    try:
        run_test()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during test: {e}")
        sys.exit(1)
