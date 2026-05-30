# 🎯 Backend — EchoScene AI Media Management

> FastAPI-based backend service for intelligent media ingestion, multimodal indexing, and semantic search.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Running the Backend](#running-the-backend)
- [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)
- [Core Services](#core-services)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Overview

The **EchoScene Backend** is a Python 3.11 FastAPI service that powers intelligent media asset management. It orchestrates:

- **Vision Captioning** — Local Ollama `llama3.2-vision` model for image/video frame descriptions
- **Speech Transcription** — OpenAI Whisper for audio-to-text indexing
- **Scene Detection** — PySceneDetect + OpenCV for frame-accurate video segmentation
- **Vector Embeddings** — Multimodal embeddings stored in ChromaDB
- **Semantic Search** — Natural language queries against the vector store
- **Asset Management** — CRUD operations on media metadata

All processing runs **locally** on your machine — no data leaves your environment.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend (5173)                    │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP/REST
                             ▼
┌─────────────────────────────────────────────────────────────┐
│         FastAPI Backend (Port 8000)                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ API Layer (/api/v1)                                 │    │
│  │  • /media        — Asset CRUD                       │    │
│  │  • /ingest       — Ingestion pipeline               │    │
│  │  • /search       — Semantic search                  │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Core Services (/core)                               │    │
│  │  • ingest/      — vision_tagger, transcriber, etc   │    │
│  │  • embeddings/  — Vector generation & storage       │    │
│  │  • search/      — Semantic query logic              │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Data Layer (/db, /repositories)                     │    │
│  │  • PostgreSQL ORM models                            │    │
│  │  • Database access layer                            │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
          ▲                  ▲                    ▲
          │                  │                    │
    ┌─────┴────┐      ┌──────┴──────┐      ┌─────┴────┐
    │PostgreSQL│      │  ChromaDB   │      │  Ollama  │
    │   5432   │      │    8000     │      │  11434   │
    └──────────┘      └─────────────┘      └──────────┘
       (Relational DB)  (Vector DB)     (Vision Model)
```

---

## Project Structure

```
backend/
├── README.md                  # This file
├── Dockerfile               # Container image definition
├── requirements.txt         # Python dependencies
│
├── main.py                  # FastAPI app initialization
├── config.py               # Environment configuration (Pydantic)
│
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI router setup
│   │
│   ├── api/               # REST API layer (v1)
│   │   ├── __init__.py
│   │   ├── dependencies.py # Shared dependencies, auth, etc.
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── routes/
│   │           ├── __init__.py
│   │           ├── assets.py     # Asset CRUD endpoints
│   │           ├── ingest.py     # Ingestion pipeline endpoints
│   │           └── search.py     # Semantic search endpoints
│   │
│   ├── core/              # Business logic layer
│   │   ├── __init__.py
│   │   ├── ingest/        # Media ingestion & processing
│   │   │   ├── __init__.py
│   │   │   ├── scene_detector.py    # PySceneDetect + OpenCV
│   │   │   ├── transcriber.py       # Whisper speech-to-text
│   │   │   ├── vision_tagger.py     # Ollama vision captioning
│   │   │   └── ingestion_service.py # Orchestrates ingest pipeline
│   │   │
│   │   ├── embeddings/    # Vector embeddings
│   │   │   ├── __init__.py
│   │   │   ├── embedder.py          # Generate embeddings
│   │   │   └── vector_store.py      # ChromaDB interface
│   │   │
│   │   └── search/        # Semantic search
│   │       ├── __init__.py
│   │       └── semantic_search.py   # Query & retrieval logic
│   │
│   ├── db/                # Database layer
│   │   ├── __init__.py
│   │   ├── database.py    # SQLAlchemy setup
│   │   └── models.py      # ORM models (Asset, Scene, etc.)
│   │
│   ├── models/            # Pydantic schemas & response models
│   │   ├── __init__.py
│   │   ├── asset.py       # Asset schema (request/response)
│   │   ├── search.py      # Search schema
│   │   └── ingest.py      # Ingest request schema
│   │
│   ├── repositories/      # Data access layer
│   │   ├── __init__.py
│   │   ├── asset_repository.py      # Asset CRUD ops
│   │   └── scene_repository.py      # Scene CRUD ops
│   │
│   ├── schemas/           # Additional data schemas
│   │   ├── __init__.py
│   │   └── responses.py   # Standard API response wrappers
│   │
│   ├── services/          # Business logic services
│   │   ├── __init__.py
│   │   └── asset_service.py         # High-level asset operations
│   │
│   └── tests/             # Unit & integration tests
│       ├── __init__.py
│       ├── test_ingest.py
│       ├── test_search.py
│       └── test_vision_tagger.py    # Vision captioning tests
│
└── data/                  # Local data directory (Docker volume)
    ├── media/             # Source media files (mounted from host)
    ├── chromadb/          # Vector store persistence
    └── uploads/           # Uploaded files from API
```

---

## Prerequisites

### 1. **System Requirements**

- **OS**: macOS, Linux, or Windows (with WSL2)
- **CPU**: 4+ cores (8+ recommended for video processing)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 50GB+ available space

### 2. **Required Software**

#### Docker & Docker Compose

```bash
# Verify installation
docker --version        # v24.0+
docker compose version  # v2.20+
```

👉 [Install Docker Desktop](https://www.docker.com/products/docker-desktop/)

#### Ollama (Local Vision Model)

```bash
# Download and install
# macOS / Linux: https://ollama.ai
# Windows: https://github.com/ollama/ollama/releases

# After installation, verify Ollama is running
ollama --version
```

#### Python 3.11+ (for local development only)

```bash
python --version  # 3.11+
```

#### FFmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows (with Chocolatey)
choco install ffmpeg

# Verify
ffmpeg -version
```

### 3. **Ollama Setup**

Before starting the backend, ensure Ollama is running and the vision model is downloaded:

```bash
# Terminal 1: Start Ollama service
ollama serve

# Terminal 2: Pull the vision model (one-time, ~7-8 GB)
ollama pull llama3.2-vision

# Verify the model is available
ollama list
# Output should show: llama3.2-vision
```

> **Important**: Ollama must be running on port `11434` before starting the backend container.

---

## Installation & Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/ntnhan19/smart_media_analytics_cloudforge.git
cd smart_media_analytics_cloudforge
```

### Step 2: Configure Environment Variables

```bash
# Copy the example .env file
cp .env.example .env

# Edit .env with your configuration
# (See Environment Variables section below)
```

### Step 3: Pull Pre-built Docker Images (Recommended for Members)

> **Why?** The backend image is ~5.66 GB and takes 10–15 minutes to build from scratch.
> Pulling from Docker Hub is significantly faster.

```bash
docker pull ntnhan1801/echoscene-backend:latest
docker pull ntnhan1801/echoscene-frontend:latest
```

Then start the full stack using the prod compose override (no build required):

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up
```

### Step 4: (Optional) Build from Source

Only needed if you are modifying the Dockerfile or dependencies:

```bash
docker compose up --build
```

### Step 5: (Optional) Local Development Setup

If you want to run the backend locally without Docker:

```bash
# Create a Python virtual environment
python -m venv venv

# Activate it
# macOS / Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Create required directories
mkdir -p data/media data/chromadb
```

---

## Running the Backend

### Option 1: Using Pre-built Images from Docker Hub ✅ Recommended for Members

This is the fastest way to get started — no build step required.

```bash
# 1. Pull images (one-time, ~6 GB total)
docker pull ntnhan1801/echoscene-backend:latest
docker pull ntnhan1801/echoscene-frontend:latest

# 2. Start the full stack
docker compose -f docker-compose.yml -f docker-compose.prod.yml up

# Expected output:
# ✓ Backend:    http://localhost:8000
# ✓ Frontend:   http://localhost:5173
# ✓ ChromaDB:   http://localhost:8001
# ✓ PostgreSQL: localhost:5432
# ✓ MinIO:      http://localhost:9000 (console: 9001)
```

To stop:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
```

---

### Option 2: Build from Source (For Backend Developers)

Use this option only when you need to modify `Dockerfile` or `requirements.txt`.

```bash
# Build and start all services
docker compose up --build

# Start in background
docker compose up --build -d
```

---

### Option 3: Run Backend Locally (Hot-Reload Development)

Start only the infrastructure services in Docker, run the backend directly on your machine.

```bash
# Step 1: Start databases only
docker compose up -d postgres chromadb minio

# Step 2: Wait for services to initialize
sleep 5

# Step 3: Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Step 4: Start FastAPI with hot-reload
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### Check Service Health

```bash
curl http://localhost:8000/health

# Expected response:
# {"status": "ok", "version": "0.1.0", "service": "echoscene-backend"}
```

### View Logs

```bash
# All services
docker compose logs -f

# Backend only
docker compose logs -f backend
```

---

## Environment Variables

Copy `.env.example` to `.env` and configure the following:

```dotenv
# =============================================================================
# AI Pipeline — Ollama (Local LLM server)
# =============================================================================
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.2-vision

# =============================================================================
# Vision Captioning Configuration
# =============================================================================
VISION_CAPTION_PROMPT_DETAIL=high            # high | low
VISION_CAPTION_MAX_TOKENS=256
VISION_CAPTION_TEMPERATURE=0.7

# =============================================================================
# ChromaDB — Vector database
# When using Docker Compose, the host is the service name "chromadb"
# When running locally, use localhost
# =============================================================================
CHROMA_HOST=chromadb                         # Docker: chromadb | Local: localhost
CHROMA_PORT=8000
CHROMA_PERSIST_PATH=/app/data/chromadb       # Inside container: /app/data/chromadb

# =============================================================================
# PostgreSQL — Relational database
# =============================================================================
DATABASE_URL=postgresql+psycopg://echoscene:echoscene_dev_password@postgres:5432/echoscene
POSTGRES_DB=echoscene
POSTGRES_USER=echoscene
POSTGRES_PASSWORD=echoscene_dev_password

# =============================================================================
# MinIO — Object storage (S3-compatible)
# =============================================================================
MINIO_ENDPOINT=minio:9000                    # Docker internal DNS
MINIO_ROOT_USER=echoscene
MINIO_ROOT_PASSWORD=echoscene_dev_password
MINIO_BUCKET_MEDIA=media
MINIO_BUCKET_THUMBNAILS=thumbnails
MINIO_USE_SSL=false

# =============================================================================
# Media & Storage paths
# =============================================================================
MEDIA_SOURCE_PATH=/app/data/media
UPLOAD_MAX_SIZE_MB=500
ALLOWED_MEDIA_TYPES=mp4,mkv,avi,mov,jpg,jpeg,png,webp

# =============================================================================
# Whisper — Speech-to-text model size
# Options: tiny (39M) | base (140M) | small (244M) | medium (769M) | large (3GB)
# Smaller models = faster but less accurate
# =============================================================================
WHISPER_MODEL_SIZE=base

# =============================================================================
# Scene Detection — PySceneDetect settings
# =============================================================================
SCENE_DETECTION_THRESHOLD=27.0               # 0.0-255.0; lower = more scenes detected

# =============================================================================
# API Settings
# =============================================================================
API_TITLE=EchoScene API
API_DESCRIPTION=Multimodal Media Search Engine
API_VERSION=0.1.0

# =============================================================================
# Logging
# =============================================================================
LOG_LEVEL=INFO                                # DEBUG | INFO | WARNING | ERROR | CRITICAL

# =============================================================================
# Optional: AWS Configuration (Production Only)
# =============================================================================
# AWS_REGION=ap-southeast-1
# AWS_S3_BUCKET=sma-media-assets
# AWS_BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
# AWS_BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
```

### Environment Variable Reference

| Variable                    | Description                  | Default                             | Required |
| --------------------------- | ---------------------------- | ----------------------------------- | -------- |
| `OLLAMA_BASE_URL`           | Ollama API endpoint          | `http://host.docker.internal:11434` | ✅ Yes   |
| `OLLAMA_MODEL`              | Vision model name            | `llama3.2-vision`                   | ✅ Yes   |
| `CHROMA_HOST`               | ChromaDB hostname            | `chromadb`                          | ✅ Yes   |
| `CHROMA_PORT`               | ChromaDB port                | `8000`                              | ✅ Yes   |
| `DATABASE_URL`              | PostgreSQL connection string | —                                   | ✅ Yes   |
| `WHISPER_MODEL_SIZE`        | Speech-to-text model         | `base`                              | ✅ Yes   |
| `SCENE_DETECTION_THRESHOLD` | Scene change sensitivity     | `27.0`                              | ❌ No    |
| `MEDIA_SOURCE_PATH`         | Local media directory        | `/app/data/media`                   | ✅ Yes   |
| `LOG_LEVEL`                 | Logging verbosity            | `INFO`                              | ❌ No    |

---

## API Documentation

### Interactive API Docs

Once the backend is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Core Endpoints

#### Health Check

```bash
GET /health

# Response:
{
  "status": "ok",
  "version": "0.1.0",
  "service": "echoscene-backend"
}
```

#### Asset Management

```bash
# List all media assets
GET /api/v1/media

# Get asset details
GET /api/v1/media/{asset_id}

# Upload a new media asset
POST /api/v1/media
Content-Type: multipart/form-data
file: <binary>

# Delete an asset
DELETE /api/v1/media/{asset_id}
```

#### Ingestion & Indexing

```bash
# Start ingesting a media file
POST /api/v1/ingest
{
  "asset_id": "uuid",
  "media_type": "video"  # "video" | "image"
}

# Get ingest job status
GET /api/v1/ingest/jobs/{job_id}
```

#### Semantic Search

```bash
# Search media assets by natural language query
GET /api/v1/search?q=sunset+over+ocean&limit=10

# Response:
{
  "query": "sunset over ocean",
  "results": [
    {
      "asset_id": "uuid",
      "title": "Beach Video",
      "similarity_score": 0.92,
      "timestamp_sec": 45.5
    }
  ]
}
```

---

## Core Services

### 1. **Vision Tagger** (`core/ingest/vision_tagger.py`)

- Accepts: image file path or video frame (numpy array from OpenCV)
- Returns: Natural language scene description via Ollama `llama3.2-vision`
- Features:
  - Base64 image encoding
  - 3-attempt retry with exponential backoff
  - Graceful fallback on connection errors
  - Async/await support

### 2. **Transcriber** (`core/ingest/transcriber.py`)

- Extracts audio from video
- Runs OpenAI Whisper for speech-to-text
- Returns: List of caption segments with timestamps

### 3. **Scene Detector** (`core/ingest/scene_detector.py`)

- Detects scene changes in videos
- Returns: Frame timecodes and keyframes for each scene

### 4. **Vector Embedder** (`core/embeddings/embedder.py`)

- Generates multimodal embeddings from text/captions
- Stores vectors in ChromaDB

### 5. **Semantic Search** (`core/search/semantic_search.py`)

- Converts natural language queries to embeddings
- Retrieves similar scenes from ChromaDB
- Returns timestamp-linked results

---

## Development Workflow

### Hot-Reload Development

When running locally or with Docker bind-mounts, changes to source code trigger automatic reloads:

```bash
# Edit a file in backend/app/
vim backend/app/api/routes/search.py

# The server automatically reloads:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Will watch for changes in these directories: ['/app']
# INFO:     Uvicorn reloading in 0.24 seconds.
```

### Useful Make Commands

```bash
# Access backend container shell
make shell-backend

# Access database shell
make shell-db

# View backend logs
make logs-backend

# Health check
make health

# Full restart
make restart
```

### Running Tests

```bash
# Inside backend container or local venv
pytest tests/ -v

# Specific test file
pytest tests/test_vision_tagger.py -v

# With coverage
pytest --cov=app tests/ -v
```

---

## Testing

### Unit Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_vision_tagger.py -v

# Single test function
pytest tests/test_vision_tagger.py::test_caption_image -v

# With coverage report
pytest --cov=app tests/
```

### Manual Integration Testing

#### Test Vision Captioning

```bash
python -c "
from app.core.ingest.vision_tagger import VisionTagger
import asyncio

tagger = VisionTagger(
    ollama_base_url='http://localhost:11434',
    model_name='llama3.2-vision'
)

caption = asyncio.run(tagger.caption_image('sample.jpg'))
print(caption)
"
```

#### Test Whisper Transcription

```bash
python -c "
from app.core.ingest.transcriber import Transcriber

transcriber = Transcriber(model_size='base')
segments = transcriber.transcribe('video.mp4')
for seg in segments:
    print(f'{seg[\"start\"]:0.1f}s - {seg[\"text\"]}')"
```

### Health Check

```bash
curl -s http://localhost:8000/health | jq .

docker compose exec postgres psql -U echoscene -d echoscene -c "SELECT 1"

curl -s http://localhost:8001/api/v1/heartbeat | jq .
```

---

## Troubleshooting

### Backend Container Fails to Start

**Error**: `Connection refused: Ollama not running`

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Pull the model
ollama pull llama3.2-vision

# Terminal 3: Start the backend
docker compose up -d backend
```

---

### "Cannot connect to PostgreSQL"

**Error**: `psycopg.OperationalError: connection failed`

```bash
docker compose ps postgres
docker compose up -d postgres
docker compose up -d backend
```

---

### "ChromaDB returns 404"

**Error**: `httpx.ConnectError: Connection refused`

```bash
docker compose ps chromadb
docker compose logs chromadb
docker compose restart chromadb
```

---

### Image Pull Fails

**Error**: `pull access denied for ntnhan1801/echoscene-backend`

```bash
# Login to Docker Hub first
docker login

# Then pull again
docker pull ntnhan1801/echoscene-backend:latest
```

---

### Vision Captioning is Very Slow

**Possible Causes**: Ollama is running on CPU (no GPU acceleration)

```bash
# Check if Ollama is using GPU
ollama list

# Enable GPU (platform-specific):
# macOS: GPU support is automatic if available
# Linux (NVIDIA): Install NVIDIA Docker runtime
# Windows: Ensure WSL2 has GPU access
```

---

### Disk Space Issues

**Error**: `No space left on device`

```bash
df -h
docker system prune -a
ollama rm llama3.2-vision   # Only if you want to free space
```

---

### Port Already in Use

**Error**: `bind: address already in use :::8000`

```bash
# macOS/Linux
lsof -i :8000

# Windows
netstat -ano | findstr :8000
```

---

### Logs Indicate "Config not found"

**Error**: `ERROR: .env file not found`

```bash
cp .env.example .env
```

---

## Performance Tips

### 1. **Whisper Model Size**

```dotenv
WHISPER_MODEL_SIZE=tiny    # Fastest, ~39 MB
WHISPER_MODEL_SIZE=base    # Balanced (recommended), ~140 MB
WHISPER_MODEL_SIZE=small   # Slower, better accuracy, ~244 MB
```

### 2. **Scene Detection Threshold**

```dotenv
SCENE_DETECTION_THRESHOLD=27.0  # Default
# Lower = more scenes detected (slower, more detailed)
# Higher = fewer scenes detected (faster, less detail)
```

---

## Useful Commands

```bash
# Quick restart
make restart

# View all container statuses
docker compose ps

# Stream logs from all services
make logs

# Shell access to backend
make shell-backend

# Run tests
pytest tests/ -v

# Check service health
make health

# Clean up everything
make clean-all
```

---

## Additional Resources

- 📖 [FastAPI Documentation](https://fastapi.tiangolo.com/)
- 🦙 [Ollama Documentation](https://github.com/ollama/ollama)
- 🗃️ [ChromaDB Documentation](https://docs.trychroma.com/)
- 🗄️ [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/)
- 🐘 [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

## Support & Contributing

For issues, questions, or contributions:

1. Check [Troubleshooting](#troubleshooting) section above
2. Review logs: `docker compose logs backend`
3. Open an issue on the repository
4. Contact the Backend Engineer (M2)

---

**Last Updated**: May 2026  
**Maintainer**: EchoScene Backend Team
