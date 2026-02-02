import time
import os
import subprocess
import random
import textwrap
import logging
from datetime import datetime

# Enable extreme verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/watcher_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
MEDIA_DIR = "/ffmpeg_media"
LOCAL_MEDIA_DIR = "/Users/kapilh/ffmpeg/media"  # Local path to copy from
POLL_INTERVAL = 2  # Seconds between scans
DEBOUNCE_TIME = 5  # Wait after last change before processing

# Version - update this to change output filenames
VERSION = "v2-cinematic"  # Updated version name

# Import cinematic utilities
from .cinematic_utils import create_cinematic_filters, create_text_overlay, CINEMATIC_VERSION

# Update version to use the one from cinematic_utils
VERSION = CINEMATIC_VERSION

# Font Registry
FONTS = {
    "classic": "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "classic_slides": "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "slides_random": "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",  # Randomizes font + colors per slide
    "slides_ultra_random": "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",  # Randomizes font + colors + TEXT per slide
    "inter": "/fonts/Inter-Bold.ttf",
    "playfair": "/fonts/PlayfairDisplay-Bold.ttf"
}

FONT_SIZES = {
    "classic": 100,
    "classic_slides": 100,
    "slides_random": 100,
    "slides_ultra_random": 100,
    "inter": 104,
    "playfair": 96
}

# Color Pairs (Background, Text) - Expanded for more variety
COLOR_PAIRS = [
    # Classic contrasts
    ("black", "white"),
    ("white", "black"),
    ("#1a1a2e", "#eaeaea"),  # Dark navy / off-white
    ("#0f0f0f", "#f5f5f5"),  # Near black / bright white
    
    # Bold primaries
    ("DarkBlue", "white"),
    ("DarkRed", "white"),
    ("#c0392b", "white"),   # Pomegranate red
    ("#2980b9", "white"),   # Belize blue
    
    # Elegant metallics
    ("Gold", "black"),
    ("#d4af37", "black"),   # Classic gold
    ("#c9b037", "#1a1a1a"), # Antique gold
    
    # Nature tones
    ("DarkGreen", "white"),
    ("#27ae60", "white"),   # Emerald
    ("Teal", "white"),
    ("#16a085", "white"),   # Green sea
    
    # Royal & luxury
    ("Purple", "white"),
    ("#8e44ad", "white"),   # Wisteria purple
    ("#6c3483", "#f8f8f8"), # Deep purple
    ("#2c3e50", "#ecf0f1"), # Midnight blue / cloud
    
    # Warm & inviting
    ("#e74c3c", "white"),   # Alizarin red
    ("#d35400", "white"),   # Pumpkin orange
    ("#f39c12", "black"),   # Sunflower yellow
    ("#e67e22", "black"),   # Carrot orange
    
    # Cool & modern
    ("#3498db", "white"),   # Peter river blue
    ("#1abc9c", "white"),   # Turquoise
    ("#9b59b6", "white"),   # Amethyst
    
    # Gradients simulated via solid
    ("#2d3436", "#dfe6e9"), # Dracula / anti-flash
    ("#636e72", "white"),   # Gray aspirin
    ("#fd79a8", "black"),   # Pink glamour
    ("#00cec9", "black"),   # Robin's egg
]

# Marketing phrases pool for randomization
MARKETING_PHRASES = [
    # Opening/Hook
    "Convert any photo into beautiful hyper personalised merch !",
    "Your face. Your style. Your merch.",
    "From selfie to stunning — in seconds",
    "Turn memories into masterpieces",
    "One photo. Infinite possibilities.",
    "Where AI meets artistry",
    
    # Gallery/Avatar
    "Browse through our gallery of lovingly curated avatars",
    "Explore 100+ stunning art styles",
    "Hand-picked designs, AI-powered magic",
    "Pick your vibe. We'll do the rest.",
    "Anime? Portrait? Fantasy? You choose.",
    "Every style tells your story",
    
    # Upload/Photo
    "Upload any photo of your choice, a selfie or wefie",
    "Just one tap to upload",
    "Solo or squad — we've got you covered",
    "Any photo. Any angle. Pure magic.",
    "Your best moments deserve the best treatment",
    "Upload in seconds. Cherish forever.",
    
    # AI Transformation
    "Create Stunningly beautiful, hyper personalised images",
    "Watch the magic unfold",
    "AI that truly sees you",
    "Hyper-realistic. Hyper-personal. Hyper-you.",
    "Crafted with precision. Designed with love.",
    "Your likeness, elevated to art",
    
    # Merch/Product
    "Get these as beautiful memories via physical merch",
    "Premium quality you can feel",
    "Canvas. Mug. Poster. Phone case. More.",
    "Gift-worthy. Wall-worthy. You-worthy.",
    "Memories you can hold",
    "From screen to your doorstep",
    
    # Call-to-Action/Closing
    "Start creating today",
    "Your personalized merch awaits",
    "Make it yours at Facemash.store",
    "Because you deserve to be art",
    "Facemash.store\\n— Where You Become The Art",
    
    # Emotional/Lifestyle
    "The perfect gift they'll never forget",
    "Celebrate YOU in stunning detail",
    "Art that's uniquely, unmistakably you",
    "Create. Print. Treasure.",
    "More than merch — it's a moment",
]

DEFAULT_OVERLAYS = [
    {"text": "Convert any photo into beautiful hyper personalised merch !", "start": 0, "end": 1},
    {"text": "Browse through our gallery of lovingly curated avatars", "start": 1, "end": 2},
    {"text": "Upload any photo of your choice, a selfie or wefie", "start": 2, "end": 3},
    {"text": "Create Stunningly beautiful, hyper personalised images", "start": 3, "end": 4},
    {"text": "Get these as beautiful memories via physical merch", "start": 4, "end": 5},
    {"text": "Facemash.store\\nHyper \\nPersonalised Merch", "start": 5, "end": 6}
]

def check_real_format(remote_path):
    """Detects if a file is JPEG or PNG using magic bytes."""
    logger.debug(f"🔍 Checking real format for: {remote_path}")
    try:
        cmd = ["docker", "exec", "ffmpeg_engine_main", "hexdump", "-n", "8", "-e", '8/1 "%02x "', remote_path]
        logger.debug(f"🔧 Running command: {' '.join(cmd)}")
        output = subprocess.check_output(cmd, text=True).strip().lower()
        logger.debug(f"📊 Hexdump output: {output}")
        if output.startswith("ff d8 ff"): 
            logger.debug(f"✅ Detected JPEG format for {remote_path}")
            return "jpeg"
        if output.startswith("89 50 4e 47"): 
            logger.debug(f"✅ Detected PNG format for {remote_path}")
            return "png"
        logger.debug(f"❓ Unknown format for {remote_path}")
        return None
    except Exception as e:
        logger.error(f"💥 Error checking format for {remote_path}: {e}")
        return None

def create_text_slide(text, font_path, output_path, font_size=100, bg_color="black", text_color="white"):
    """Generates a 1600x1600 image with centered text on colored background."""
    # Wrap text to width 20
    wrapped_text = textwrap.fill(text, width=20)
    safe_text = wrapped_text.replace(":", "\\:").replace("'", "'\\\\\\''")
    
    cmd = [
        "docker", "exec", "ffmpeg_engine_main", "ffmpeg",
        "-f", "lavfi", "-i", f"color=c={bg_color}:s=1600x1600:d=1",
        "-vf", f"drawtext=fontfile='{font_path}':text='{safe_text}':x=(w-text_w)/2:y=(h-text_h)/2:fontsize={font_size}:fontcolor={text_color}:borderw=4:bordercolor=black",
        "-frames:v", "1",
        "-y", output_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating text slide: {e.stderr.decode()}", flush=True)
        return False

def get_music_files():
    """Lists .mp3 files in /music container path."""
    try:
        cmd = ["docker", "exec", "ffmpeg_engine_main", "ls", "/music"]
        output = subprocess.check_output(cmd, text=True)
        return [f for f in output.splitlines() if f.lower().endswith('.mp3')]
    except Exception:
        return []

def get_audio_duration(track_path):
    """Gets duration of audio file using ffprobe in container."""
    try:
        cmd = [
            "docker", "exec", "ffmpeg_engine_main", 
            "ffprobe", "-v", "error", "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", track_path
        ]
        output = subprocess.check_output(cmd, text=True).strip()
        return float(output)
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
    print(f"Generating video for user: {uuid} with normalization and font variations...", flush=True)
    
    # Step 1: Normalize everything to standard JPEGs (ONCE per job)
    image_files = normalize_to_jpegs(uuid, image_files)
    if not image_files:
        print(f"No valid images after normalization for {uuid}", flush=True)
        return

    remote_proc_dir = os.path.join(uuid, "_processing")
    
    # Load overlays from JSON if available, else use defaults
    overlays = DEFAULT_OVERLAYS
    try:
        import json
        ov_path = os.path.join(MEDIA_DIR, uuid, "overlays.json")
        if os.path.exists(ov_path):
            with open(ov_path, 'r') as f:
                overlays = json.load(f)
    except Exception as e:
        print(f"Error loading overlays.json for {uuid}, using defaults: {e}", flush=True)

    # Step 2: Prepare Music Selection
    # Seed random with Run Name (uuid) for deterministic base
    random.seed(uuid)
    
    music_files = get_music_files()
    
    # Step 3: Render a separate video for each font variation
    print(f"DEBUG: Font keys to process: {list(FONTS.keys())}", flush=True)
    for font_id, font_path in FONTS.items():
        print(f"DEBUG: Starting font_id: {font_id}", flush=True)
        try:
            # Check if font actually exists inside the container before attempting render
            check_font = ["docker", "exec", "ffmpeg_engine_main", "test", "-f", font_path]
            if subprocess.run(check_font).returncode != 0:
                print(f"Font render skipped: {font_id} (not found) for uuid {uuid}", flush=True)
                continue
            
            # --- Sequence Generation Logic ---
            is_slides_mode = "slides" in font_id
            current_proc_dir = remote_proc_dir # Default to normalized images
            video_duration = len(image_files)

            if is_slides_mode:
                # Create dedicated directory for interleaved slides
                slides_proc_dir = os.path.join(uuid, f"_processing_{font_id}")
                remote_slides_dir = slides_proc_dir
                subprocess.run(["docker", "exec", "ffmpeg_engine_main", "mkdir", "-p", remote_slides_dir], check=True)
                
                # Interleave Strategy: [Text 0] -> [Img 0] -> [Text 1] -> [Img 1] ...
                generated_count = 0
                for i, img_file in enumerate(image_files):
                    # 1. Generate Text Slide (Even indices: 0000, 0002, ...)
                    text_idx = i * 2
                    
                    # Determine text content based on mode
                    if font_id == "slides_ultra_random":
                        # Pick completely random text from MARKETING_PHRASES pool
                        text_content = random.choice(MARKETING_PHRASES)
                    elif i < len(overlays):
                        text_content = overlays[i]['text']
                    elif MARKETING_PHRASES:
                        # Fallback to random marketing phrase when overlays run out
                        text_content = random.choice(MARKETING_PHRASES)
                    else:
                        text_content = " "
                    
                    # Determine styling
                    slide_font = font_path
                    slide_bg = "black"
                    slide_fg = "white"
                    
                    if font_id in ("slides_random", "slides_ultra_random"):
                        # Pick a random font from available list (deduped paths)
                        available_font_paths = list(set(FONTS.values()))
                        slide_font = random.choice(available_font_paths)
                        # Pick random colors
                        slide_bg, slide_fg = random.choice(COLOR_PAIRS)
                        
                        print(f"DEBUG: [{font_id}] Slide {i} for {uuid} | Text: '{text_content[:20]}...' | Font: {os.path.basename(slide_font)} | BG: {slide_bg} | FG: {slide_fg}", flush=True)

                    slide_path = f"{remote_slides_dir}/{text_idx:04d}.jpg"
                    
                    create_text_slide(text_content, slide_font, slide_path, font_size=FONT_SIZES.get(font_id, 100), bg_color=slide_bg, text_color=slide_fg)
                    
                    # 2. Copy/Link Image (Odd indices: 0001, 0003, ...)
                    img_idx = i * 2 + 1
                    src_img_path = f"{remote_proc_dir}/{img_file}" # e.g. _processing/0000.jpg
                    dest_img_path = f"{remote_slides_dir}/{img_idx:04d}.jpg"
                    
                    # Using cp to copy from normalized dir to slides dir
                    subprocess.run(["docker", "exec", "ffmpeg_engine_main", "cp", src_img_path, dest_img_path], check=True)
                    generated_count += 2
                
                current_proc_dir = remote_slides_dir
                video_duration = generated_count # 1s per slide/photo
            
            # --- Music Selection Logic ---
            # Reseed per variation to ensure diff track/slice but stable for this specific output
            random.seed(f"{uuid}_{font_id}")
            
            selected_track_path = None
            slice_start = 0.0
            
            if music_files:
                # Try up to 3 times to find a valid track
                for _ in range(3):
                    track_name = random.choice(music_files)
                    track_path = f"/music/{track_name}"
                    duration = get_audio_duration(track_path)
                    
                    if duration and duration > 0:
                        # Success
                        selected_track_path = track_path
                        if duration <= video_duration:
                            slice_start = 0.0
                        else:
                            max_start = duration - video_duration
                            slice_start = random.uniform(0, max_start)
                        break
            
            # Create cinematic filters
            cinematic = create_cinematic_filters(
                len(image_files),
                duration_per_image=3.0,
                preset="default"  # Can be "default", "dramatic", or "subtle"
            )
            
            # Build the FFmpeg command
            cmd = ["docker", "exec", "ffmpeg_engine_main", "ffmpeg", "-y"]
            
            # Input images
            cmd.extend([
                "-framerate", "1/3",  # 3 seconds per image
                "-i", f"{current_proc_dir}/%04d.jpg"
            ])
            
            # Input audio (if any)
            if selected_track_path:
                cmd.extend([
                    "-ss", str(slice_start),
                    "-t", str(len(image_files) * 3),  # 3 seconds per image
                    "-i", selected_track_path
                ])
            
            # Video filters
            vf_parts = cinematic["video_filters"]
            
            # Add text overlays
            for ov in overlays:
                text_filter = create_text_overlay(
                    text=ov['text'],
                    start_time=ov['start'],
                    end_time=ov['end'],
                    font_path=font_path
                )
                vf_parts.append(text_filter)
            
            # Join all video filters
            cmd.extend(["-vf", ",".join(vf_parts)])
            
            # Video codec settings
            cmd.extend([
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-r", "30"  # Ensure 30fps output
            ])
            
            # Audio settings (if audio exists)
            if selected_track_path:
                cmd.extend([
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-af", ",".join(cinematic["audio_filters"]),
                    "-shortest"
                ])
            
            # Output file with version in the name
            output_filename = f"output_video_{font_id}_{VERSION}.mp4"
            cmd.append(f"{uuid}/{output_filename}")
            
            # Run the command
            try:
                print(f"Running FFmpeg command: {' '.join(cmd)}", flush=True)
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                print(f"FFmpeg output: {result.stdout}", flush=True)
                if result.stderr:
                    print(f"FFmpeg warnings: {result.stderr}", flush=True)
                print(f"Successfully generated {output_filename} for {uuid}", flush=True)
                return True
            except subprocess.CalledProcessError as e:
                print(f"FFmpeg error: {e.stderr}", flush=True)
                return False
            except Exception as e:
                print(f"Unexpected error: {str(e)}", flush=True)
                return False

        except subprocess.CalledProcessError as e:
            # Log font-specific failure but continue with remaining fonts
            print(f"Font render failed: {font_id} for uuid {uuid}", flush=True)
            print(f"FFmpeg error: {e.stderr.decode()}", flush=True)
            continue
        except Exception as e:
            print(f"Unexpected error rendering font {font_id} for {uuid}: {e}", flush=True)
            continue

    # Step 3: Cleanup processing dir after ALL font renders are finished
    try:
        subprocess.run(["docker", "exec", "ffmpeg_engine_main", "rm", "-rf", remote_proc_dir], check=True)
        # Cleanup slide dirs if any
        subprocess.run(["docker", "exec", "ffmpeg_engine_main", "sh", "-c", f"rm -rf {MEDIA_DIR}/{uuid}/_processing_*"], check=True)
    except Exception as e:
        print(f"Error during cleanup for {uuid}: {e}", flush=True)

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

def copy_local_to_docker(local_dir, docker_dir):
    """Copy files from local directory to Docker container only when needed."""
    logger.debug(f"🔄 Starting copy check from {local_dir} to {docker_dir}")
    try:
        # Ensure local directory exists
        if not os.path.exists(local_dir):
            logger.debug(f"❌ Local directory {local_dir} does not exist")
            return False
            
        # Get subdirectories in local path
        local_subdirs = [d for d in os.listdir(local_dir) if os.path.isdir(os.path.join(local_dir, d))]
        logger.debug(f"📁 Found local subdirs: {local_subdirs}")
        
        files_copied = 0
        for subdir in local_subdirs:
            local_subdir_path = os.path.join(local_dir, subdir)
            docker_subdir_path = os.path.join(docker_dir, subdir)
            
            # Get local files with their modification times
            local_files = {}
            for file in os.listdir(local_subdir_path):
                local_file_path = os.path.join(local_subdir_path, file)
                if os.path.isfile(local_file_path):
                    local_files[file] = os.path.getmtime(local_file_path)
            
            if not local_files:
                logger.debug(f"📂 No files in {local_subdir_path}")
                continue
            
            # Create directory in Docker container
            subprocess.run(["docker", "exec", "ffmpeg_engine_main", "mkdir", "-p", docker_subdir_path], 
                         check=True, capture_output=True)
            
            # Check which files need copying
            for file, local_mtime in local_files.items():
                local_file_path = os.path.join(local_subdir_path, file)
                docker_file_path = os.path.join(docker_subdir_path, file)
                
                # Check if file exists in Docker and compare modification times
                needs_copy = False
                try:
                    # Get Docker file modification time
                    docker_mtime_cmd = ["docker", "exec", "ffmpeg_engine_main", "stat", "-c", "%Y", docker_file_path]
                    docker_mtime = float(subprocess.check_output(docker_mtime_cmd, text=True).strip())
                    
                    if local_mtime > docker_mtime:
                        needs_copy = True
                        logger.debug(f"🔄 File {file} needs update (local: {local_mtime}, docker: {docker_mtime})")
                    else:
                        logger.debug(f"✅ File {file} is up to date")
                except subprocess.CalledProcessError:
                    # File doesn't exist in Docker, needs copying
                    needs_copy = True
                    logger.debug(f"📥 File {file} doesn't exist in Docker, needs copying")
                
                if needs_copy:
                    docker_dest = f"ffmpeg_engine_main:{docker_subdir_path}/{file}"
                    subprocess.run(["docker", "cp", local_file_path, docker_dest], check=True, capture_output=True)
                    logger.debug(f"📤 Copied {file} to Docker")
                    files_copied += 1
                    
            if files_copied > 0:
                logger.info(f"📦 Copied {files_copied} files from {local_subdir_path} to {docker_subdir_path}")
        
        logger.debug(f"✅ Copy check completed. {files_copied} files copied.")
        return files_copied > 0
    except Exception as e:
        logger.error(f"💥 Error copying local to Docker: {e}")
        return False

def get_remote_now():
    try:
        output = subprocess.check_output(["docker", "exec", "ffmpeg_engine_main", "date", "+%s"], text=True).strip()
        return float(output)
    except Exception:
        return time.time()

def main():
    logger.info(f"🎬 Watcher [{VERSION}] started | Polling: {MEDIA_DIR} | Local: {LOCAL_MEDIA_DIR} | Fonts: {len(FONTS)} | Colors: {len(COLOR_PAIRS)} | Phrases: {len(MARKETING_PHRASES)}")
    print(f"🎬 Watcher [{VERSION}] started | Polling: {MEDIA_DIR} | Local: {LOCAL_MEDIA_DIR} | Fonts: {len(FONTS)} | Colors: {len(COLOR_PAIRS)} | Phrases: {len(MARKETING_PHRASES)}", flush=True)
    processed_state = {}

    while True:
        try:
            # Step 1: Copy files from local to Docker (only if needed)
            copy_start = time.time()
            files_updated = copy_local_to_docker(LOCAL_MEDIA_DIR, MEDIA_DIR)
            copy_time = time.time() - copy_start
            logger.debug(f"⏱️ Copy step took {copy_time:.2f}s")
            
            # Step 2: Scan Docker directory for processing
            subdirs = list_subdirs(MEDIA_DIR)
            logger.debug(f"📁 Found subdirs: {subdirs}")
            print(f"📁 Checking subfolders: {subdirs}", flush=True)
            
            if not subdirs:
                logger.debug("⏸️ No subfolders found, waiting...")
                print("⏸️  No subfolders found, waiting...", flush=True)
                time.sleep(POLL_INTERVAL)
                continue
                
            now = get_remote_now()
            
            for i, uuid in enumerate(subdirs):
                # Show which folder we're checking and what's next
                next_folder = subdirs[i + 1] if i + 1 < len(subdirs) else "None"
                logger.debug(f"🔍 Checking folder: {uuid} | Next: {next_folder}")
                print(f"🔍 Checking folder: {uuid} | Next: {next_folder}", flush=True)
                
                path = os.path.join(MEDIA_DIR, uuid)
                image_files = list_image_files(path)
                logger.debug(f"📸 Found {len(image_files)} image files in {uuid}")
                print(f"   📸 Found {len(image_files)} image files in {uuid}", flush=True)
                
                if not image_files:
                    logger.debug(f"⏭️ Skipping {uuid} - no image files")
                    print(f"   ⏭️  Skipping {uuid} - no image files", flush=True)
                    continue
                
                mtimes = []
                for f in image_files:
                    mt = get_remote_mtime(os.path.join(path, f))
                    if mt > 0: mtimes.append(mt)
                
                if not mtimes:
                    logger.debug(f"⏭️ Skipping {uuid} - no valid file timestamps")
                    print(f"   ⏭️  Skipping {uuid} - no valid file timestamps", flush=True)
                    continue
                    
                max_mtime = max(mtimes)
                
                # Check if already processed
                if uuid in processed_state and max_mtime <= processed_state[uuid]:
                    time_since_change = now - max_mtime
                    logger.debug(f"✅ {uuid} already processed (stable for {time_since_change:.1f}s)")
                    print(f"   ✅ {uuid} already processed (stable for {time_since_change:.1f}s)", flush=True)
                    continue
                
                time_since_change = now - max_mtime
                if time_since_change > DEBOUNCE_TIME:
                    logger.info(f"🚀 Processing {uuid} ({len(image_files)} files, stable for {time_since_change:.1f}s)")
                    print(f"   🚀 Processing {uuid} ({len(image_files)} files, stable for {time_since_change:.1f}s)", flush=True)
                    run_ffmpeg_robust(uuid, image_files)
                    processed_state[uuid] = max_mtime
                    logger.info(f"✅ Completed processing {uuid}")
                    print(f"   ✅ Completed processing {uuid}", flush=True)
                else:
                    logger.debug(f"⏳ Waiting for {uuid} to stabilize ({time_since_change:.1f}s / {DEBOUNCE_TIME}s)")
                    print(f"   ⏳ Waiting for {uuid} to stabilize ({time_since_change:.1f}s / {DEBOUNCE_TIME}s)", flush=True)
            
            cycle_time = time.time() - copy_start
            logger.debug(f"⏱️ Full cycle took {cycle_time:.2f}s")
            print(f"⏱️  Cycle complete, next check in {POLL_INTERVAL}s...", flush=True)
            time.sleep(POLL_INTERVAL)
        except Exception as e:
            logger.error(f"❌ Error in polling loop: {e}", exc_info=True)
            print(f"❌ Error in polling loop: {e}", flush=True)
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
