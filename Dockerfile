FROM python:3.11-slim

# Install system dependencies & FFmpeg for Discord voice/audio streaming
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libnacl-dev \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Run the 24/7 Keep-Alive Supervisor
CMD ["python", "keep_alive_supervisor.py"]
