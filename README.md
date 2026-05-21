# Smart Media Analytics (SMA)

> An AI-powered, Local-First Media Asset Management and Semantic Search System — built for Video Editors and Designers who need to search mixed local media assets using natural language and seek to exact timestamps.

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

**Smart Media Analytics (SMA)** is a local-first media asset management system that lets creative professionals — video editors and designers — ingest, index, and semantically search through large libraries of images and videos without relying on cloud infrastructure during day-to-day use.

Under the hood, SMA uses multimodal AI models for visual understanding, automatic speech recognition for dialogue and narration indexing, and scene-change detection to build a frame-accurate, searchable knowledge base of every asset in your library.

When you're ready to scale, SMA's architecture maps cleanly onto AWS production targets (S3, Bedrock, Transcribe, OpenSearch Serverless) with minimal refactoring.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Natural Language Search** | Query your media library in plain English — "sunset over the ocean with ambient music" |
| 🎞️ **Timestamp-Level Seek** | Search results link directly to the exact second inside a video where a scene or phrase occurs |
| 🖼️ **Multimodal Indexing** | Images and videos are described by a local vision-language model (LLaVA / llama3.2-vision) |
| 🎙️ **Speech Transcription** | Audio tracks are transcribed via OpenAI Whisper and stored for full-text semantic search |
| 🎬 **Automatic Scene Detection** | PySceneDetect + OpenCV split videos into meaningful scenes before indexing |
| 🗂️ **Asset Management** | Browse, preview, tag, and organize all local media from a single React dashboard |
| 📦 **Local-First, Privacy-Safe** | All processing runs on your machine via Docker — no data leaves your environment |
| ☁️ **Cloud-Ready Architecture** | Drop-in AWS Bedrock, S3, Transcribe, and OpenSearch Serverless for production scale |

---

## 🛠️ Tech Stack

### Local Development Stack

| Layer | Technology |
|---|---|
| **Frontend** | React.js (Vite), Tailwind CSS |
| **Backend API** | Python 3.11, FastAPI, Uvicorn |
| **Vision AI** | Ollama — `llama3.2-vision` (local LLM inference) |
| **Speech-to-Text** | OpenAI Whisper (local, runs via Python) |
| **Video Processing** | FFmpeg, OpenCV, PySceneDetect |
| **Vector Database** | ChromaDB (embedded, local) |
| **Orchestration** | Docker Compose |

### ☁️ AWS Production Targets

| Local Component | AWS Equivalent |
|---|---|
| Local file storage | **Amazon S3** |
| Ollama (vision + embeddings) | **AWS Bedrock** — Claude 3.5 Sonnet + Titan Embeddings |
| OpenAI Whisper | **Amazon Transcribe** |
| ChromaDB | **Amazon OpenSearch Serverless** |

---

## 📁 Project Structure
sma/
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

---

## 🚀 Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v24+)
- [Ollama](https://ollama.ai/) installed on the host machine
- [Node.js](https://nodejs.org/) (v18+) — for local frontend dev only
- [Python](https://www.python.org/) 3.11+ — for local backend dev only
- FFmpeg available on `$PATH`

---

### Step 1 — Pull the Vision Model via Ollama

Ollama must be running on the host before starting Docker services. The backend communicates with Ollama at `http://host.docker.internal:11434`.

```bash
# Start the Ollama service
ollama serve

# Pull the multimodal vision model (in a separate terminal)
ollama pull llama3.2-vision
```

> **Note:** `llama3.2-vision` is approximately 7–8 GB. Ensure you have sufficient disk space and that Ollama is accessible on port `11434`.

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

### Step 3 — Start All Services with Docker Compose

```bash
# Build and start backend + frontend containers
docker compose up --build

# Or run in detached mode
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
| ChromaDB (internal) | http://localhost:8001 |

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
