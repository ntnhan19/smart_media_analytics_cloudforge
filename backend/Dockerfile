# =============================================================================
# EchoScene — Backend Dockerfile
# Base image: python:3.11-slim (lightweight, suitable for production)
# Owner: M2 (Backend Engineer)
# =============================================================================

FROM python:3.11-slim

# Metadata
LABEL maintainer="EchoScene Team"
LABEL description="FastAPI backend for EchoScene AI media management"

# ---------------------------------------------------------------------------
# System dependencies
# ffmpeg  — required by Whisper and OpenCV for video/audio processing
# curl    — used by Docker healthcheck
# libgl1  — required by OpenCV for OpenGL support
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# ---------------------------------------------------------------------------
# Install Python dependencies first (leverage Docker layer cache)
# Copy only requirements.txt first — if source code changes but deps do not,
# Docker skips the pip install step entirely
# ---------------------------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy full source code into the container
# (In dev mode, the bind-mount will override this directory)
COPY . .

# Create data directories if they do not exist
RUN mkdir -p /app/data/media /app/data/chromadb

# Expose FastAPI port
EXPOSE 8000

# ---------------------------------------------------------------------------
# Entrypoint — run uvicorn with hot-reload for development
# --host 0.0.0.0  required to accept connections from outside the container
# --reload        auto-restart on code changes (dev only)
# ---------------------------------------------------------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
