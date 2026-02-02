# FFmpeg Cinematic Video Generator

A powerful Docker-based service that automatically generates cinematic videos from images with professional effects, color grading, and animated text overlays.

## Version: v2-cinematic

## Architecture

This project consists of two main Docker services:

1. **FFmpeg Engine (`ffmpeg_engine_main`)**: A container with FFmpeg 4.4 for video processing.
2. **File Watcher (`file_watcher_main`)**: A Python-based service that monitors directories and orchestrates cinematic video generation.

## Features

### Cinematic Effects
- **Smooth Zoom Effects**: Professional zoom-in/out animations
- **Color Grading**: Professional color correction with contrast, saturation, and warmth adjustments
- **Animated Text Overlays**: Fade in/out text animations with customizable borders
- **Audio Processing**: Fade in/out effects for background music
- **Multiple Presets**: Choose from default, dramatic, or subtle cinematic styles

### Core Features
- **Automated Polling**: Watches for new subdirectories in the `media/` folder
- **Content Debouncing**: Waits for file upload completion before processing
- **Image Normalization**: Converts various formats to standard JPEG
- **Font Variations**: Multiple font styles (Classic, Inter, Playfair)
- **Cleanup**: Automatic removal of temporary files

## Setup & Usage

### Prerequisites
- Docker and Docker Compose installed

### Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/eunginx/ffmpeg.git
    cd ffmpeg
    ```

2. Build and start the services:
    ```bash
    docker-compose up -d --build
    ```

3. Test the cinematic effects:
    ```bash
    python test_cinematic.py
    ```

### How to Use

1. Create a new subdirectory inside the `media/` folder (e.g., `media/user_001/`)
2. Add image files (`.jpg`, `.png`) to this folder
3. Optionally add music files to the `music/` directory
4. The watcher will generate cinematic videos with names like `output_video_classic_v2-cinematic.mp4`

## Cinematic Presets

### Default
- Zoom factor: 1.04x
- Duration: 2.5s
- Contrast: 1.08
- Saturation: 1.06
- Text fade: 0.5s

### Dramatic
- Zoom factor: 1.08x
- Duration: 3.0s
- Higher contrast and saturation
- Longer text animations

### Subtle
- Zoom factor: 1.02x
- Duration: 2.0s
- Light color adjustments
- Quick text fades

## Configuration

### Environment Variables
- `CINEMATIC_VERSION`: Version identifier (default: v2-cinematic)
- `PYTHONUNBUFFERED`: Python output buffering

### File Configuration
- `MEDIA_DIR`: Directory to watch (default: `/ffmpeg_media`)
- `POLL_INTERVAL`: Scan frequency (default: 2 seconds)
- `DEBOUNCE_TIME`: Stability wait time (default: 5 seconds)

### Custom Presets
Edit `watcher/cinematic_utils.py` to create custom cinematic presets:
```python
"my_preset": {
    "zoom": {"factor": 1.05, "duration": 2.0},
    "color": {"contrast": 1.1, "saturation": 1.05},
    "text": {"fade_duration": 0.4}
}
```

## File Structure

```
ffmpeg/
├── watcher/
│   ├── watcher.py           # Main orchestration script
│   ├── cinematic_utils.py   # Cinematic effects utilities
│   └── Dockerfile          # Watcher service build
├── media/                  # Input/output directory
├── music/                  # Background music files
├── test_cinematic.py       # Test script
├── docker-compose.yml      # Service definitions
└── requirements.txt        # Python dependencies
```

## Output

Videos are generated with the naming convention:
`output_video_{font_style}_{version}.mp4`

Example:
- `output_video_classic_v2-cinematic.mp4`
- `output_video_inter_v2-cinematic.mp4`
- `output_video_playfair_v2-cinematic.mp4`

## Troubleshooting

### Check Container Logs
```bash
docker-compose logs file_watcher_main
docker-compose logs ffmpeg_engine_main
```

### Common Issues
1. **No video generated**: Check if images are in the correct directory
2. **FFmpeg errors**: Verify container has access to media files
3. **Font issues**: Ensure fonts are properly mounted in the container

## Version History
- **v2-cinematic**: Added cinematic effects, color grading, and text animations
- **v1-initial**: Basic video generation with text overlays
