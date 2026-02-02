# FFmpeg Watcher Service

A hyper-reliable Docker-based service that watches a directory for new images and automatically generates videos with text overlays using FFmpeg.

## Architecture

This project consists of two main Docker services:

1.  **FFmpeg Engine (`ffmpeg_engine_main`)**: A lightweight Alpine-based container with FFmpeg installed.
2.  **File Watcher (`file_watcher_main`)**: A Python-based service that monitors the `media/` directory and orchestrates video generation via the FFmpeg engine.

## Features

- **Automated Polling**: Watches for new subdirectories in the `media/` folder.
- **Content Debouncing**: Waits for a stable period after the last modification before processing to ensure all files are uploaded.
- **Image Normalization**: Automatically converts various image formats (JPEG, PNG) to a standard format for consistent video generation.
- **Dynamic Text Overlays**: Adds custom text overlays to the generated video.
- **Cleanup**: Automatically removes temporary processing files after video generation.

## Setup & Usage

### Prerequisites

- Docker and Docker Compose installed.

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/eunginx/ffmpeg.git
    cd ffmpeg
    ```

2.  Build and start the services:
    ```bash
    docker-compose up -d --build
    ```

### How to Use

1.  Create a new subdirectory inside the `media/` folder (e.g., `media/user_001/`).
2.  Add image files (`.jpg`, `.png`, etc.) to this folder.
3.  The watcher will detect the changes, wait for stability, and generate an `output_video.mp4` inside the same subdirectory.

## Configuration

- `MEDIA_DIR`: The directory to watch (default: `/ffmpeg_media`).
- `POLL_INTERVAL`: Frequency of directory scans (default: 2 seconds).
- `DEBOUNCE_TIME`: Stability wait time before processing (default: 5 seconds).

## Local Development

The project structure is as follows:
- `docker-compose.yml`: Defines the service stack.
- `media/`: The host directory for input and output files (ignored by git).
- `watcher/`: Contains the watcher logic.
  - `Dockerfile`: Build instructions for the watcher service.
  - `watcher.py`: The core Python polling and orchestration script.
