FROM python:3.11-slim

# Install system dependencies: FFmpeg and libopus for high-fidelity Discord voice/music
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libopus0 \
        libopus-dev \
        ca-certificates \
        git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot source code
COPY . .

# Expose Render default web port
EXPOSE 10000

# Start both bots + Render health server 24/7
CMD ["python", "-u", "run_24_7.py"]
