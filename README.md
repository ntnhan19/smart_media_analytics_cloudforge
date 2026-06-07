# 🎬 Smart Media Analytics (SMA)

> An AI-powered, Local-First Media Asset Management and Semantic Search System — built for Video Editors and Designers who need to search mixed local media assets using natural language and seek [...]

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Core API Data Contract](#core-api-data-contract)
- [Team Roles](#team-roles)
- [Roadmap](#roadmap)

---

## Overview

**Smart Media Analytics (SMA)** is a local-first media asset management system that lets creative professionals — video editors and designers — ingest, index, and semantically search through l[...]

Under the hood, SMA uses multimodal AI models for visual understanding, automatic speech recognition for dialogue and narration indexing, and scene-change detection to build a frame-accurate, sear[...]

When you're ready to scale, SMA's architecture maps cleanly onto AWS production targets (S3, Bedrock, Transcribe, OpenSearch Serverless) with minimal refactoring.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Natural Language Search** | Query your media library in plain English — "sunset over the ocean with ambient music" |
| 🎞️ **Timestamp-Level Seek** | Search results link directly to the exact second inside a video where a scene or phrase occurs |
| 🖼️ **Multimodal Indexing** | Videos are described by Qwen2.5-VL running locally via Ollama — no cloud API required |
| 🎙️ **Speech Transcription** | Audio tracks are transcribed via faster-whisper (ctranslate2 backend, CPU-optimized) |
| 🎬 **Automatic Scene Detection** | PySceneDetect splits videos into meaningful scenes before indexing |
| 🗂️ **Asset Management** | Browse, preview, tag, and organize all local media from a single React dashboard |
| 📦 **Local-First, Privacy-Safe** | All processing runs on your machine via Docker — no data leaves your environment |
| ☁️ **Cloud-Ready Architecture** | Drop-in AWS Bedrock, S3, Transcribe, and OpenSearch Serverless for production scale |

---

## 🛠️ Tech Stack

### Local Development Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19 (Vite), Tailwind CSS |
| **Backend API** | Python 3.11, FastAPI, Uvicorn |
| **Vision AI** | Ollama — `qwen2.5vl:3b` (local multimodal inference) |
| **Speech-to-Text** | `faster-whisper` — ctranslate2 backend, CPU-optimized |
| **Embeddings** | Ollama — `bge-m3:latest` (1024-dim dense vectors) |
| **Video Processing** | FFmpeg, OpenCV (headless), PySceneDetect 0.6.4 |
| **Vector Database** | ChromaDB 1.5.9 (HTTP client mode) |
| **Relational Database** | PostgreSQL 16 |
| **Object Storage** | MinIO (S3-compatible, local) |
| **Orchestration** | Docker Compose |

### ☁️ AWS Production Targets

| Local Component | AWS Equivalent |
|---|---|
| MinIO | **Amazon S3** |
| Ollama `qwen2.5vl:3b` | **AWS Bedrock** — Claude 3.5 Sonnet |
| Ollama `bge-m3:latest` | **AWS Bedrock** — Titan Embeddings v2 |
| faster-whisper | **Amazon Transcribe** |
| ChromaDB | **Amazon OpenSearch Serverless** |
| PostgreSQL | **Amazon RDS PostgreSQL** |

---

## 📁 Project Structure

```
smart_media_analytics_cloudforge/
├── docker-compose.yml
├── .env.example
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Env-based configuration
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── assets.py          # Asset CRUD endpoints
│   │   │   ├── ingest.py          # Ingest & indexing pipeline
│   │   │   └── search.py          # Semantic search endpoints
│   │   └── dependencies.py
│   │
│   ├── core/
│   │   ├── ingest/
│   │   │   ├── scene_detector.py  # PySceneDetect + OpenCV
│   │   │   ├── transcriber.py     # Whisper ASR wrapper
│   │   │   └── vision_tagger.py   # Ollama vision captioning
│   │   ├── embeddings/
│   │   │   ├── embedder.py        # Embedding generation
│   │   │   └── vector_store.py    # ChromaDB interface
│   │   └── search/
│   │       └── semantic_search.py # Query + retrieval logic
│   │
│   ├── models/
│   │   ├── asset.py               # Pydantic data models
│   │   └── search.py
│   │
│   └── tests/
│       ├── test_ingest.py
│       └── test_search.py
│
├── frontend/
│   ├── Dockerfile
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── package.json
│   │
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       │
│       ├── components/
│       │   ├── SearchBar/
│       │   ├── AssetGrid/
│       │   ├── VideoPlayer/       # Timestamp-seek enabled player
│       │   ├── IngestPanel/
│       │   └── TagBadge/
│       │
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── Search.jsx
│       │   └── AssetDetail.jsx
│       │
│       ├── hooks/
│       │   ├── useSearch.js
│       │   └── useIngest.js
│       │
│       └── services/
│           └── api.js             # Axios API client
│
└── data/
    ├── media/                     # Drop source assets here
    ├── chromadb/                  # Persisted vector store
    └── whisper_cache/             # Cached Whisper model weights
```

---

## 🚀 Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v24+)
- [Ollama](https://ollama.com/) installed and running on the host machine
- Git

> **Local dev only (no Docker):** Node.js v18+, Python 3.11+, FFmpeg on `$PATH`

---

### Step 1 — Pull AI Models via Ollama

Ollama must be running on the host before starting Docker services. The backend communicates with it at `http://host.docker.internal:11434`.

```bash
# Start Ollama (if not already running as a system service)
ollama serve

# Pull the vision model (~2 GB)
ollama pull qwen2.5vl:3b

# Pull the embedding model (~1.2 GB)
ollama pull bge-m3:latest
```

> **Note:** Ensure Ollama is accessible on port `11434` before starting Docker services.

---

### Step 2 — Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and fill in the required values:

```dotenv
# --- Backend ---
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.2-vision
CHROMA_PERSIST_PATH=/app/data/chromadb
MEDIA_SOURCE_PATH=/app/data/media
WHISPER_MODEL_SIZE=base          # tiny | base | small | medium | large

# --- Frontend ---
VITE_API_BASE_URL=http://localhost:8000

# --- AWS (optional, production only) ---
AWS_REGION=ap-southeast-1
AWS_S3_BUCKET=sma-media-assets
AWS_BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
AWS_BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
```

---

### Step 3 — Start All Services

#### 🚀 Quick Start — Use pre-built images (recommended for team members)

```bash
# Uses images published to Docker Hub — no local build needed
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# View logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# Stop all services
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
```

#### 🔧 Full Build — Build images locally (for contributors)

```bash
# Build and start all services from source
docker compose up --build -d

# View logs
docker compose logs -f backend
docker compose logs -f frontend
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| ChromaDB | http://localhost:8001 |
| MinIO Console | http://localhost:9001 |
| PostgreSQL | localhost:5433 |

---

### Step 4 — Local Backend Development (without Docker)

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server with hot-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

### Step 5 — Local Frontend Development (without Docker)

```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```

The Vite dev server proxies API requests to `http://localhost:8000` automatically via `vite.config.js`.

---

### Step 6 — Ingest Your First Assets

1. Drop your media files (`.mp4`, `.mov`, `.jpg`, `.png`, etc.) into `data/media/`.
2. Open the SMA dashboard at http://localhost:5173.
3. Click **"Ingest Assets"** — SMA will scan, process, and index all detected files.
4. Use the **Search** bar to query your library in natural language.

---

## 📡 Core API Data Contract

### `POST /api/v1/ingest` — Trigger Ingestion Pipeline

**Request**
```json
{
  "source_path": "/app/data/media",
  "options": {
    "scene_detection": true,
    "transcription": true,
    "vision_caption": true,
    "whisper_model": "base"
  }
}
```

**Response**
```json
{
  "job_id": "ingest-20240821-001",
  "status": "processing",
  "assets_queued": 14,
  "message": "Ingestion pipeline started successfully."
}
```

---

### `POST /api/v1/search` — Semantic Search

**Request**
```json
{
  "query": "person walking on a beach during golden hour",
  "filters": {
    "media_type": ["video", "image"],
    "tags": []
  },
  "top_k": 5
}
```

**Response**
```json
{
  "query": "person walking on a beach during golden hour",
  "results": [
    {
      "asset_id": "vid-0042",
      "file_name": "vacation_reel_2024.mp4",
      "media_type": "video",
      "file_path": "/app/data/media/vacation_reel_2024.mp4",
      "thumbnail_url": "/thumbnails/vid-0042-scene3.jpg",
      "score": 0.94,
      "scene": {
        "scene_index": 3,
        "timestamp_start_sec": 142.5,
        "timestamp_end_sec": 161.0,
        "caption": "A person strolls along a sandy beach as the sun sets, casting a warm golden light across the water.",
        "transcript_snippet": "This was the most peaceful evening of the whole trip."
      },
      "tags": ["beach", "golden hour", "walking", "outdoors"]
    },
    {
      "asset_id": "img-0117",
      "file_name": "golden_beach_portrait.jpg",
      "media_type": "image",
      "file_path": "/app/data/media/golden_beach_portrait.jpg",
      "thumbnail_url": "/thumbnails/img-0117.jpg",
      "score": 0.88,
      "scene": null,
      "tags": ["beach", "portrait", "golden hour", "sunset"]
    }
  ],
  "total_results": 2,
  "processing_time_ms": 312
}
```

---

### `GET /api/v1/assets/{asset_id}` — Get Asset Detail

**Response**
```json
{
  "asset_id": "vid-0042",
  "file_name": "vacation_reel_2024.mp4",
  "media_type": "video",
  "duration_sec": 312.4,
  "resolution": "1920x1080",
  "file_size_bytes": 248310784,
  "ingested_at": "2024-08-21T09:15:42Z",
  "scenes": [
    {
      "scene_index": 0,
      "timestamp_start_sec": 0.0,
      "timestamp_end_sec": 48.2,
      "caption": "Aerial drone footage over a mountain range at dawn.",
      "transcript_snippet": "We started the trip early to catch the sunrise."
    },
    {
      "scene_index": 3,
      "timestamp_start_sec": 142.5,
      "timestamp_end_sec": 161.0,
      "caption": "A person strolls along a sandy beach as the sun sets.",
      "transcript_snippet": "This was the most peaceful evening of the whole trip."
    }
  ],
  "full_transcript": "We started the trip early to catch the sunrise. [...]",
  "tags": ["travel", "beach", "mountain", "drone", "golden hour"]
}
```

---

## 👥 Team Roles

| Member | Role | Responsibilities |
|---|---|---|
| **Member 1** | Team Lead / Systems Architect | Overall system design, Docker Compose orchestration, cloud-to-local architecture mapping, AWS production planning, code review |
| **Member 2** | AI / Data Engineer | Ollama vision captioning pipeline, Whisper transcription integration, ChromaDB vector schema, embedding strategy, semantic search tuning |
| **Member 3** | Backend Engineer | FastAPI routes and middleware, ingest pipeline orchestration, FFmpeg + PySceneDetect integration, API data contracts, testing |
| **Member 4** | Frontend Engineer | React dashboard, Vite + Tailwind setup, video player with timestamp-seek, asset grid, search UX, API integration via Axios |

---

## 🗺️ Roadmap

- [ ] Local ingest pipeline (vision, ASR, scene detection)
- [ ] ChromaDB vector store with semantic search
- [ ] React dashboard with timestamp-seek video player
- [ ] Batch ingest progress tracking with WebSocket updates
- [ ] Multi-user asset tagging and annotation
- [ ] AWS Bedrock + S3 production deployment guide
- [ ] Amazon OpenSearch Serverless migration script
- [ ] Clip export — save search-result segments as new files
- [ ] Fine-tuned embedding model on domain-specific media vocabulary

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with ❤️ by the CloudForge Team
</p>
