import time
import os
import subprocess
import random
import textwrap
from datetime import datetime

# Configuration
MEDIA_DIR = "/ffmpeg_media"
POLL_INTERVAL = 2  # Seconds between scans
DEBOUNCE_TIME = 5  # Wait after last change before processing

# Version - update this to change output filenames
VERSION = "v1-initial"

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
    try:
        cmd = ["docker", "exec", "ffmpeg_engine_main", "hexdump", "-n", "8", "-e", '8/1 "%02x "', remote_path]
        output = subprocess.check_output(cmd, text=True).strip().lower()
        if output.startswith("ff d8 ff"): return "jpeg"
        if output.startswith("89 50 4e 47"): return "png"
        return None
    except Exception:
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
            
            # -----------------------------

            print(f"Rendering variation for {uuid} with font: {font_id}", flush=True)
            if selected_track_path:
                print(f"  Music: {selected_track_path} (Start: {slice_start:.2f}s, Dur: {video_duration}s)", flush=True)
            else:
                print(f"  Music: None (Silent fallback)", flush=True)
            


            
            
            if is_slides_mode:
                # No overlays needed, text is baked into slides
                vf_string = "pad=ceil(iw/2)*2:ceil(ih/2)*2" 
            else:
                font_size = FONT_SIZES.get(font_id, 50)
                filter_parts = [
                    "pad=ceil(iw/2)*2:ceil(ih/2)*2" # Ensure even dims (non-negotiable)
                ]
                
                for ov in overlays:
                    # Wrap text to avoid overflow
                    wrapped_text = textwrap.fill(ov['text'], width=20)
                    
                    # Escape ":" and "'" for FFmpeg drawtext
                    safe_text = wrapped_text.replace(":", "\\:").replace("'", "'\\\\\\''")
                    # Add fade-out in last 0.2 seconds
                    fade_duration = 0.2
                    alpha_expr = f"if(lt(t,{ov['end']}-{fade_duration}),1,({ov['end']}-t)/{fade_duration})"
                    filter_parts.append(
                        f"drawtext=fontfile='{font_path}':text='{safe_text}':enable='between(t,{ov['start']},{ov['end']})':"
                        f"x=0.18*w+(0.64*w-text_w)/2:y=0.18*h+(0.64*h-text_h)/2:fontsize={font_size}:fontcolor=white:borderw=4:bordercolor=black:alpha='{alpha_expr}'"
                    )
                vf_string = ",".join(filter_parts)
            # Use version-based filename: output_video_{font_id}_{VERSION}.mp4
            output_filename = f"output_video_{font_id}_{VERSION}.mp4"
            
            # Construct FFmpeg command with correct argument order:
            # inputs -> filters -> encoding -> output
            
            cmd = ["docker", "exec", "ffmpeg_engine_main", "ffmpeg"]
            
            # Input 1: Images
            cmd.extend([
                "-framerate", "1",
                "-i", f"{current_proc_dir}/%04d.jpg"
            ])
            
            # Input 2: Audio (if selected)
            if selected_track_path:
                cmd.extend([
                    "-ss", str(slice_start),
                    "-t", str(video_duration),
                    "-i", selected_track_path
                ])
            
            # Output Options
            cmd.extend([
                "-vf", vf_string,
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p"
            ])
            
            if selected_track_path:
                cmd.extend([
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-af", "volume=0.9",
                    "-shortest"
                ])
            
            cmd.extend([
                "-y",
                f"{uuid}/{output_filename}"
            ])
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"Successfully generated {output_filename} for {uuid}", flush=True)

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

def get_remote_now():
    try:
        output = subprocess.check_output(["docker", "exec", "ffmpeg_engine_main", "date", "+%s"], text=True).strip()
        return float(output)
    except Exception:
        return time.time()

def main():
    print(f"🎬 Watcher [{VERSION}] started | Polling: {MEDIA_DIR} | Fonts: {len(FONTS)} | Colors: {len(COLOR_PAIRS)} | Phrases: {len(MARKETING_PHRASES)}", flush=True)
    processed_state = {}

    while True:
        try:
            subdirs = list_subdirs(MEDIA_DIR)
            print(f"DEBUG: Found subdirs: {subdirs}", flush=True)
            now = get_remote_now()
            
            for uuid in subdirs:
                print(f"DEBUG: Checking uuid: {uuid}", flush=True)
                path = os.path.join(MEDIA_DIR, uuid)
                image_files = list_image_files(path)
                print(f"DEBUG: Found {len(image_files)} image files in {uuid}", flush=True)
                
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
