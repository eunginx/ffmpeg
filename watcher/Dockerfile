FROM jrottenberg/ffmpeg:4.4-ubuntu

# Install Python and required packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    fonts-dejavu \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Create necessary directories
RUN mkdir -p /ffmpeg_media /music

# Copy your code
COPY . /app
WORKDIR /app

# Add fonts (create fonts directory if you have custom fonts, otherwise use system fonts)
RUN mkdir -p /usr/share/fonts/truetype
# COPY fonts /usr/share/fonts/truetype/  # Uncomment if you have custom fonts directory

# Set environment variables
ENV PYTHONPATH=/app
ENV CINEMATIC_VERSION=v2-cinematic

# Command to run your watcher
CMD ["python3", "watcher.py"]
