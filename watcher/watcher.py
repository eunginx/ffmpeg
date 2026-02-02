import time
import os
import subprocess

# Configuration
MEDIA_DIR = "/ffmpeg_media"
POLL_INTERVAL = 2  # Seconds between scans
DEBOUNCE_TIME = 5  # Wait after last change before processing

def check_real_format(remote_path):
    """Detects if a file is JPEG or PNG using magic bytes."""
    try:
        cmd = ["docker", "exec", "ffmpeg_engine_main", "hexdump", "-n", "8", "-e", '8/1 "%02x "', remote_path]
        output = subprocess.check_output(cmd, text=True).strip().lower()
        if output.startswith("ff d8 ff"): return "jpeg"
        if output.startswith("89 50 4e 47"): return "png"
        return None
    except Exception:
        return None

def normalize_to_jpegs(uuid, files):
    """Converts all files to standard JPEGs in a _processing subdir."""
    proc_dir = os.path.join(MEDIA_DIR, uuid, "_processing")
    remote_proc_dir = os.path.join(uuid, "_processing")
    
    # Create processing dir inside container
    subprocess.run(["docker", "exec", "ffmpeg_engine_main", "mkdir", "-p", remote_proc_dir], check=True)
    
    normalized_list = []
    for i, f in enumerate(sorted(files)):
        target_name = f"{i:04d}.jpg"
        input_path = os.path.join(uuid, f)
        output_path = os.path.join(remote_proc_dir, target_name)
        
        # Use FFmpeg to convert/normalize to JPEG. This handles any format/ext mismatch.
        # -q:v 2 for high quality
        cmd = [
            "docker", "exec", "ffmpeg_engine_main", "ffmpeg",
            "-i", input_path,
            "-pix_fmt", "yuvj420p",
            "-q:v", "2",
            "-y", output_path
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            normalized_list.append(target_name)
        except subprocess.CalledProcessError as e:
            print(f"Error normalizing {f}: {e.stderr.decode()}", flush=True)
            
    return normalized_list

def run_ffmpeg_robust(uuid, image_files):
    print(f"Generating video for user: {uuid} with normalization and overlays...", flush=True)
    
    # Step 1: Normalize everything to standard JPEGs
    image_files = normalize_to_jpegs(uuid, image_files)
    if not image_files:
        print(f"No valid images after normalization for {uuid}", flush=True)
        return

    # Step 2: Generate video from the normalized sequence with text overlays
    remote_proc_dir = os.path.join(uuid, "_processing")
    
    # Text overlays for first 3 frames (1s each)
    # Note: colons in text MUST be escaped for drawtext filter
    overlays = [
        {"text": "From this", "start": 0, "end": 1},
        {"text": "to :", "start": 1, "end": 2},
        {"text": "Voila !!", "start": 2, "end": 3}
    ]
    
    font_path = "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"
    filter_parts = [
        "pad=ceil(iw/2)*2:ceil(ih/2)*2" # Ensure even dims
    ]
    
    for ov in overlays:
        safe_text = ov['text'].replace(":", "\\:")
        filter_parts.append(
            f"drawtext=fontfile='{font_path}':text='{safe_text}':enable='between(t,{ov['start']},{ov['end']})':"
            f"x=(w-text_w)/2:y=(h-text_h-100):fontsize=50:fontcolor=white:borderw=2:bordercolor=black"
        )
    
    vf_string = ",".join(filter_parts)
    
    cmd = [
        "docker", "exec", "ffmpeg_engine_main", "ffmpeg",
        "-framerate", "1",
        "-i", f"{remote_proc_dir}/%04d.jpg",
        "-vf", vf_string,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-y",
        f"{uuid}/output_video.mp4"
    ]
    try:
        subprocess.run(cmd, check=True)
        print(f"Successfully generated video for {uuid}", flush=True)
        # Cleanup
        subprocess.run(["docker", "exec", "ffmpeg_engine_main", "rm", "-rf", remote_proc_dir], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error generating video for {uuid}: {e}", flush=True)

def list_subdirs(parent):
    try:
        cmd = ["docker", "exec", "ffmpeg_engine_main", "ls", "-F", parent]
        output = subprocess.check_output(cmd, text=True)
        # Filter for directories only, and ignore _processing if it exists
        return [line.rstrip('/') for line in output.splitlines() if line.endswith('/') and "_processing" not in line]
    except Exception:
        return []

def list_image_files(path):
    try:
        cmd = ["docker", "exec", "ffmpeg_engine_main", "ls", path]
        output = subprocess.check_output(cmd, text=True)
        # Only pick common image formats
        extensions = ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')
        return [f for f in output.splitlines() if f.endswith(extensions) and f != "output_video.mp4" and "_processing" not in f]
    except Exception:
        return []

def get_remote_mtime(path):
    try:
        cmd = ["docker", "exec", "ffmpeg_engine_main", "stat", "-c", "%Y", path]
        output = subprocess.check_output(cmd, text=True).strip()
        return float(output)
    except Exception:
        return 0.0

def get_remote_now():
    try:
        output = subprocess.check_output(["docker", "exec", "ffmpeg_engine_main", "date", "+%s"], text=True).strip()
        return float(output)
    except Exception:
        return time.time()

def main():
    print(f"Watcher service starting - hyper-reliable remote polling {MEDIA_DIR}...", flush=True)
    processed_state = {}

    while True:
        try:
            subdirs = list_subdirs(MEDIA_DIR)
            now = get_remote_now()
            
            for uuid in subdirs:
                path = os.path.join(MEDIA_DIR, uuid)
                image_files = list_image_files(path)
                
                if not image_files:
                    continue
                
                mtimes = []
                for f in image_files:
                    mt = get_remote_mtime(os.path.join(path, f))
                    if mt > 0: mtimes.append(mt)
                
                if not mtimes:
                    continue
                    
                max_mtime = max(mtimes)
                
                if uuid not in processed_state or max_mtime > processed_state[uuid]:
                    time_since_change = now - max_mtime
                    if time_since_change > DEBOUNCE_TIME:
                        print(f"Detected stable content in {uuid} ({len(image_files)} files, stable for {time_since_change:.1f}s). Processing...", flush=True)
                        run_ffmpeg_robust(uuid, image_files)
                        processed_state[uuid] = max_mtime
                    else:
                        # Only log once per change window to avoid noise
                        pass
            
            time.sleep(POLL_INTERVAL)
        except Exception as e:
            print(f"DEBUG: Error in polling loop: {e}", flush=True)
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
