# 🎬 Smart Media Analytics (SMA)

> An AI-powered Media Asset Management and Semantic Search System — built for professionals who need to search mixed media assets using natural language and seek to exact timestamps.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture & Features](#architecture--features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Core API Data Contract](#core-api-data-contract)
- [Team Roles](#team-roles)
- [Roadmap](#roadmap)

---

## Overview

**Smart Media Analytics (SMA)** is a media asset management system that lets creative professionals ingest, index, and semantically search through large volumes of unorganized videos and images.

Under the hood, SMA uses multimodal AI models for visual understanding, automatic speech recognition for dialogue and narration indexing, and scene-change detection to build a frame-accurate, searchable vector database.

The system is designed with a **cloud-ready event-driven architecture**, decoupling heavy AI processing from the core API to ensure high scalability and responsiveness.

---

## ✨ Architecture & Features

| Feature | Description |
|---|---|
| 🔍 **Natural Language Search** | Query your media library in plain English — "sunset over the ocean with ambient music" |
| 🎞️ **Timestamp-Level Seek** | Search results link directly to the exact second inside a video where a scene or phrase occurs |
| 🎬 **Automatic Scene Detection** | PySceneDetect splits videos into meaningful scenes before indexing |
| 🎙️ **Speech Transcription** | Audio tracks are transcribed via Whisper ASR models |
| 🖼️ **Multimodal Indexing** | Visual content is processed and captioned by Vision-Language Models |
| ☁️ **Event-Driven AI Worker** | Heavy AI inference tasks are fully decoupled from the Backend API, running as isolated, scalable workers (AWS ECS Fargate) triggered by event buses. |
| 🔄 **Real-time Updates** | WebSocket integration ensures the frontend dashboard instantly reflects pipeline progress and asset states. |
| 🛡️ **Reliability** | Comprehensive unit testing suite (pytest) ensuring the integrity of the Ingest and Search pipelines. |

---

## 🛠️ Tech Stack

### Core Technologies
| Layer | Technology |
|---|---|
| **Frontend** | React 19 (Vite), Tailwind CSS |
| **Backend API** | Python 3.11, FastAPI, Uvicorn |
| **Database & Vector Store** | PostgreSQL 16 with `pgvector` extension |
| **Video Processing** | FFmpeg, OpenCV (headless), PySceneDetect |
| **AI/ML** | Whisper, Ollama |
| **Real-time** | WebSockets (FastAPI) |
| **Testing** | Pytest |

### Cloud & DevOps (AWS)
| Component | Technology |
|---|---|
| **Orchestration** | AWS Step Functions, Amazon EventBridge |
| **Compute (API)** | AWS ECS / EC2 |
| **Compute (AI Worker)** | AWS ECS Fargate (On-demand execution for cost optimization) |
| **Storage** | Amazon S3 |
| **Database** | Amazon RDS for PostgreSQL |
| **CI/CD** | GitHub Actions |
| **Containerization** | Docker, Docker Compose |

---

## 📁 Project Structure

```
smart_media_analytics_cloudforge/
├── .github/
│   └── workflows/           # CI/CD pipelines
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            
│   ├── api/                 # REST endpoints and WebSockets
│   ├── core/                # Business logic and AI integrations
│   ├── models/              # Pydantic data models
│   └── tests/               # Pytest unit tests
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/                 # React components, pages, and hooks
└── data/                    # Local storage mounts for DB and media
```

---

## 🚀 Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v24+)
- Git

### Quick Start (Docker Compose)

The easiest way to run the entire stack locally (Frontend, Backend, Database) is via Docker Compose.

```bash
# Clone the repository
git clone https://github.com/ntnhan19/smart_media_analytics_cloudforge.git
cd smart_media_analytics_cloudforge

# Setup environment variables
cp .env.example .env

# Build and start all services
docker compose up --build -d

# View logs
docker compose logs -f backend
```

| Service | URL |
|---|---|
| Frontend Dashboard | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger UI) | http://localhost:8000/docs |

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
    "vision_caption": true
  }
}
```

### `POST /api/v1/search` — Semantic Search

**Request**
```json
{
  "query": "person walking on a beach during golden hour",
  "top_k": 5
}
```

*For full API documentation, start the backend and visit the auto-generated Swagger UI at `/docs`.*

---

## 👥 Team Roles

This project was built collaboratively by a team of 4. Responsibilities included:

| Role | Responsibilities |
|---|---|
| **Systems Architect & DevOps** | Decoupled AI Worker architecture, AWS ECS Fargate deployment, Step Functions orchestration, CI/CD pipeline setup (GitHub Actions), WebSocket stabilization, Unit Testing (pytest). |
| **AI / Data Engineer** | Vision captioning pipeline, Whisper transcription integration, vector embedding strategy, `pgvector` schema design, semantic search tuning. |
| **Backend Engineer** | FastAPI routes and middleware, ingest pipeline orchestration, FFmpeg + PySceneDetect integration, API data contracts. |
| **Frontend Engineer** | React dashboard, Vite + Tailwind setup, video player with timestamp-seek, asset grid, search UX, API integration. |

---

## 🗺️ Roadmap & Progress

- [x] Local ingest pipeline (vision, ASR, scene detection)
- [x] React dashboard with timestamp-seek video player
- [x] Batch ingest progress tracking with WebSocket updates
- [x] Decouple AI Worker and deploy to AWS ECS Fargate
- [x] Cloud pipeline orchestration via AWS Step Functions
- [x] Migrate Vector DB to `pgvector` on Amazon RDS
- [x] CI/CD Pipeline via GitHub Actions
- [x] Unit Testing suite for core APIs
- [ ] Multi-user asset tagging and annotation
- [ ] Clip export — save search-result segments as new files

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with ❤️ by the CloudForge Team
</p>
