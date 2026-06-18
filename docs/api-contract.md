# SMA (Smart Media Analytics) — API Data Contract

**Version:** `v0.0.2-data-contract`
**Status:** Authoritative — Do not modify without team review
**Last Updated:** 2026-06-18

---

## Overview

This document is the **single source of truth** for all request/response schemas across the SMA platform. It defines the shared interface contract between:

| Layer | Team Member | Role |
|-------|-------------|------|
| **M1** | AI Pipeline Engineer | Produces ingestion results, scene data, captions, transcripts |
| **M2** | Backend Engineer | Implements FastAPI endpoints, enforces these schemas via Pydantic |
| **M3** | Frontend Engineer | Consumes these schemas to build React UI components |

> **Rule:** All field names are `snake_case`. All timestamps are ISO 8601 UTC. All IDs are strings.

---

## Base URL

| Environment | Base URL |
|-------------|----------|
| Local Dev   | `http://localhost:8000` |
| Docker      | `http://backend:8000` |
| AWS (future)| `https://api.echoscene.io` |

---

## Table of Contents

1. [POST /api/v1/ingest](#1-post-apiv1ingest)
2. [GET /api/v1/ingest/status/{job_id}](#2-get-apiv1ingeststatusjob_id)
3. [POST /api/v1/search](#3-post-apiv1search)
4. [GET /api/v1/assets](#4-get-apiv1assets)
5. [GET /api/v1/assets/{asset_id}](#5-get-apiv1assetsasset_id)
6. [POST /api/v1/assets/{asset_id}/reingest](#6-post-apiv1assetsasset_idreingest)
7. [POST /api/v1/assets/{asset_id}/regenerate-insights](#7-post-apiv1assetsasset_idregenerate-insights)
8. [WebSocket: ws/ingest/{job_id}](#8-websocket-wsingestjob_id)
9. [Shared Enums & Types](#9-shared-enums--types)
10. [Error Response Schema](#10-error-response-schema)

---

## 1. POST /api/v1/ingest

Triggers the AI ingestion pipeline for a given media source directory.

**Owner:** M2 (backend endpoint) + M1 (pipeline consumer)

### Request Body

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

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_path` | `string` | ✅ | Absolute path to the media directory or single file |
| `options.scene_detection` | `boolean` | ✅ | Run PySceneDetect to split video into scenes |
| `options.transcription` | `boolean` | ✅ | Run Whisper ASR for audio transcription |
| `options.vision_caption` | `boolean` | ✅ | Run Llama 3.2 Vision for scene captioning |
| `options.whisper_model` | `enum` | ✅ | Whisper model size: `tiny` \| `base` \| `small` \| `medium` \| `large` |

### Response Body — `202 Accepted`

```json
{
  "job_id": "ingest-20240821-001",
  "status": "queued",
  "assets_queued": 14,
  "message": "Ingestion pipeline started."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | `string` | Unique job identifier. Format: `ingest-YYYYMMDD-NNN` |
| `status` | `enum` | `queued` \| `processing` \| `done` \| `failed` |
| `assets_queued` | `integer` | Number of media files discovered and queued |
| `message` | `string` | Human-readable status message |

---

## 2. GET /api/v1/ingest/status/{job_id}

Polls the current status and progress of a running ingestion job.

**Owner:** M2 (backend) + M3 (frontend polling fallback)

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | `string` | The job ID returned from POST /api/v1/ingest |

### Response Body — `200 OK`

```json
{
  "job_id": "ingest-20240821-001",
  "status": "processing",
  "progress_pct": 57,
  "assets_total": 14,
  "assets_processed": 8,
  "current_file": "vacation_reel_2024.mp4",
  "started_at": "2024-08-21T09:15:42Z",
  "updated_at": "2024-08-21T09:18:05Z",
  "error_message": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | `string` | Job identifier |
| `status` | `enum` | `queued` \| `processing` \| `done` \| `failed` |
| `progress_pct` | `integer` | 0–100 completion percentage |
| `assets_total` | `integer` | Total assets in this job |
| `assets_processed` | `integer` | Assets fully processed so far |
| `current_file` | `string \| null` | Filename currently being processed |
| `started_at` | `string` | ISO 8601 UTC timestamp |
| `updated_at` | `string` | ISO 8601 UTC timestamp of last update |
| `error_message` | `string \| null` | Populated only when `status` is `failed` |

---

## 3. POST /api/v1/search

Performs semantic vector search over ingested media assets.

**Owner:** M2 (backend) + M3 (frontend search UI)

### Request Body

```json
{
  "query": "person walking on a beach at sunset",
  "filters": {
    "media_type": ["video", "image"],
    "tags": [],
    "asset_id": "vid-0042"
  },
  "top_k": 5
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | `string` | ✅ | Natural language search query |
| `filters.media_type` | `string[]` | ❌ | Filter by type: `video` \| `image` \| `audio`. Empty = all |
| `filters.tags` | `string[]` | ❌ | Filter by tags. Empty = no tag filter |
| `filters.asset_id` | `string` | ❌ | Filter by specific asset ID (In-Video Search support) |
| `top_k` | `integer` | ❌ | Max results to return. Default: `10`, Max: `50` |

### Response Body — `200 OK`

```json
{
  "query": "person walking on a beach at sunset",
  "total_results": 5,
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
        "caption": "A person walks along a sandy beach at golden hour.",
        "transcript_snippet": "This was the most peaceful evening."
      },
      "tags": ["beach", "golden hour", "walking", "outdoors"]
    }
  ]
}
```

#### Top-Level Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `query` | `string` | Echo of the original query |
| `total_results` | `integer` | Number of results returned |
| `results` | `SearchResult[]` | Array of result objects |

#### SearchResult Object

| Field | Type | Description |
|-------|------|-------------|
| `asset_id` | `string` | Unique asset identifier |
| `file_name` | `string` | Original filename |
| `media_type` | `enum` | `video` \| `image` \| `audio` |
| `file_path` | `string` | Absolute path on server |
| `thumbnail_url` | `string` | Relative URL to scene thumbnail |
| `score` | `float` | Cosine similarity score, 0.0–1.0 |
| `scene` | `SceneSnippet` | The matching scene details |
| `tags` | `string[]` | Auto-generated semantic tags |

#### SceneSnippet Object

| Field | Type | Description |
|-------|------|-------------|
| `scene_index` | `integer` | Zero-based scene index within the asset |
| `timestamp_start_sec` | `float` | Scene start time in seconds |
| `timestamp_end_sec` | `float` | Scene end time in seconds |
| `caption` | `string` | Vision model caption for this scene |
| `transcript_snippet` | `string \| null` | Short transcript excerpt for this scene |

---

## 4. GET /api/v1/assets

Returns a paginated list of all ingested assets.

**Owner:** M2 (backend) + M3 (frontend asset library view)

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | `integer` | `1` | Page number (1-indexed) |
| `page_size` | `integer` | `20` | Items per page. Max: `100` |
| `media_type` | `string` | `null` | Filter: `video` \| `image` \| `audio` |
| `sort_by` | `string` | `ingested_at` | Sort field: `ingested_at` \| `file_name` \| `duration_sec` |
| `sort_order` | `string` | `desc` | `asc` \| `desc` |

### Response Body — `200 OK`

```json
{
  "page": 1,
  "page_size": 20,
  "total_assets": 142,
  "total_pages": 8,
  "assets": [
    {
      "asset_id": "vid-0042",
      "file_name": "vacation_reel_2024.mp4",
      "media_type": "video",
      "duration_sec": 312.4,
      "resolution": "1920x1080",
      "file_size_bytes": 248310784,
      "thumbnail_url": "/thumbnails/vid-0042-scene0.jpg",
      "ingested_at": "2024-08-21T09:15:42Z",
      "tags": ["travel", "beach", "mountain"]
    }
  ]
}
```

#### Pagination Envelope

| Field | Type | Description |
|-------|------|-------------|
| `page` | `integer` | Current page number |
| `page_size` | `integer` | Items per page |
| `total_assets` | `integer` | Total assets across all pages |
| `total_pages` | `integer` | Total number of pages |
| `assets` | `AssetSummary[]` | Array of asset summary objects |

#### AssetSummary Object

| Field | Type | Description |
|-------|------|-------------|
| `asset_id` | `string` | Unique asset identifier |
| `file_name` | `string` | Original filename |
| `media_type` | `enum` | `video` \| `image` \| `audio` |
| `duration_sec` | `float \| null` | Duration in seconds (null for images) |
| `resolution` | `string \| null` | e.g. `1920x1080` (null for audio) |
| `file_size_bytes` | `integer` | File size in bytes |
| `thumbnail_url` | `string \| null` | URL to representative thumbnail |
| `ingested_at` | `string` | ISO 8601 UTC timestamp |
| `tags` | `string[]` | Auto-generated semantic tags |

---

## 5. GET /api/v1/assets/{asset_id}

Returns the full detail of a single asset including all scenes.

**Owner:** M2 (backend) + M3 (frontend asset detail view)

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `asset_id` | `string` | The unique asset ID |

### Response Body — `200 OK`

```json
{
  "asset_id": "vid-0042",
  "file_name": "vacation_reel_2024.mp4",
  "media_type": "video",
  "duration_sec": 312.4,
  "resolution": "1920x1080",
  "file_size_bytes": 248310784,
  "file_path": "/app/data/media/vacation_reel_2024.mp4",
  "ingested_at": "2024-08-21T09:15:42Z",
  "summary": "A beautiful cinematic travel vlog showcasing the natural beauty of Sweden.",
  "moods": [
    { "label": "CALM", "score": 0.95 },
    { "label": "RELAXING", "score": 0.85 }
  ],
  "objects": [
    {
      "name": "BRIDGE",
      "occurrences": [
        { "timestamp_start_sec": 0.0, "timestamp_end_sec": 1.6, "confidence": 0.95 },
        { "timestamp_start_sec": 3.2, "timestamp_end_sec": 4.8, "confidence": 0.88 }
      ]
    }
  ],
  "best_for": [
    { "name": "TRAVEL FILM", "category": "theme", "source": "auto" }
  ],
  "scenes": [
    {
      "scene_index": 0,
      "timestamp_start_sec": 0.0,
      "timestamp_end_sec": 48.2,
      "caption": "Aerial drone footage over mountains at dawn.",
      "transcript_snippet": "We started early to catch the sunrise.",
      "thumbnail_url": "/thumbnails/vid-0042-scene0.jpg",
      "embedding_id": "emb-vid0042-s0"
    }
  ],
  "full_transcript": "We started early to catch the sunrise. The mountains were covered in mist...",
  "tags": [
    { "name": "travel", "category": "theme", "source": "auto" },
    { "name": "sweden", "category": "location", "source": "auto" }
  ]
}
```

#### AssetDetail Object

| Field | Type | Description |
|-------|------|-------------|
| `asset_id` | `string` | Unique asset identifier |
| `file_name` | `string` | Original filename |
| `media_type` | `enum` | `video` \| `image` \| `audio` |
| `duration_sec` | `float \| null` | Duration in seconds |
| `resolution` | `string \| null` | e.g. `1920x1080` |
| `file_size_bytes` | `integer` | File size in bytes |
| `file_path` | `string` | Absolute server path |
| `ingested_at` | `string` | ISO 8601 UTC timestamp |
| `summary` | `string \| null` | AI-generated summary of the entire asset |
| `moods` | `MoodDetail[]` | Array of detected moods |
| `objects` | `DetectedObjectDetail[]` | Aggregated detected objects with occurrences |
| `best_for` | `TagDetail[]` | Recommendations/best-for tags |
| `scenes` | `SceneDetail[]` | All scenes for this asset |
| `full_transcript` | `string \| null` | Complete transcript (null for images) |
| `tags` | `TagDetail[]` | Auto-generated categorised semantic tags |

#### MoodDetail Object

| Field | Type | Description |
|-------|------|-------------|
| `label` | `string` | Name of the mood (e.g., `"CALM"`, `"RELAXING"`) |
| `score` | `float` | AI confidence score, 0.0–1.0 |

#### DetectedObjectDetail Object

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | UPPERCASE name of the object (e.g., `"BRIDGE"`, `"CAR"`) |
| `occurrences` | `OccurrenceDetail[]` | Array of timestamps and confidences where the object appears |

#### OccurrenceDetail Object

| Field | Type | Description |
|-------|------|-------------|
| `timestamp_start_sec` | `float` | Start time in seconds |
| `timestamp_end_sec` | `float` | End time in seconds |
| `confidence` | `float` | AI confidence score, 0.0–1.0 |

#### TagDetail Object

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Name of the tag |
| `category` | `enum` | Group classification: `"location"` \| `"content_type"` \| `"theme"` |
| `source` | `enum` | Source of the tag: `"auto"` (AI-generated) \| `"user_confirmed"` |

#### SceneDetail Object

| Field | Type | Description |
|-------|------|-------------|
| `scene_index` | `integer` | Zero-based scene index |
| `timestamp_start_sec` | `float` | Scene start in seconds |
| `timestamp_end_sec` | `float` | Scene end in seconds |
| `caption` | `string` | Vision model caption |
| `transcript_snippet` | `string \| null` | Transcript excerpt for this scene |
| `thumbnail_url` | `string \| null` | URL to scene thumbnail |
| `embedding_id` | `string` | ChromaDB/FAISS vector ID for this scene |

---

## 6. POST /api/v1/assets/{asset_id}/reingest

Triggers video re-analysis and scene detection. Utilises **Atomic Swap** (replaces old data only on 100% success) and returns a Job ID for tracking.

**Owner:** M2 (backend) + M3 (frontend)

### Request Body

```json
{
  "options": {
    "scene_detection": true,
    "transcription": true,
    "vision_caption": true
  }
}
```

### Response Body — `202 Accepted`

```json
{
  "job_id": "job-reingest-20240821-002",
  "status": "queued",
  "message": "Re-ingestion pipeline started."
}
```

---

## 7. POST /api/v1/assets/{asset_id}/regenerate-insights

Triggers LLM/Vision analysis on existing keyframes to regenerate metadata (summary, moods, objects, tags) without running scene detection or vector embeddings. Runs asynchronously.

**Owner:** M2 (backend) + M3 (frontend)

### Response Body — `202 Accepted`

```json
{
  "job_id": "job-regen-20240821-003",
  "status": "queued",
  "message": "Regenerate insights job started."
}
```

---

## 8. WebSocket: ws/ingest/{job_id}

Real-time push updates for ingestion progress. Replaces polling for the frontend.

**Owner:** M2 (backend) + M3 (frontend progress UI)

**URL:** `ws://localhost:8000/ws/ingest/{job_id}`

### Connection Lifecycle

```
Client                          Server
  |                               |
  |--- WS Connect --------------->|
  |<-- {"event": "connected"} ----|
  |                               |
  |<-- {"event": "progress"} -----|  (repeated)
  |<-- {"event": "progress"} -----|
  |                               |
  |<-- {"event": "completed"} ----|  (or "failed")
  |--- WS Close ----------------->|
```

### Event: `connected`

```json
{
  "event": "connected",
  "job_id": "ingest-20240821-001",
  "message": "Subscribed to job updates."
}
```

### Event: `progress`

```json
{
  "event": "progress",
  "job_id": "ingest-20240821-001",
  "progress_pct": 57,
  "assets_processed": 8,
  "assets_total": 14,
  "current_file": "vacation_reel_2024.mp4",
  "timestamp": "2024-08-21T09:18:05Z"
}
```

### Event: `completed`

```json
{
  "event": "completed",
  "job_id": "ingest-20240821-001",
  "progress_pct": 100,
  "assets_processed": 14,
  "assets_total": 14,
  "timestamp": "2024-08-21T09:22:31Z"
}
```

### Event: `failed`

```json
{
  "event": "failed",
  "job_id": "ingest-20240821-001",
  "progress_pct": 57,
  "error_message": "CUDA out of memory on file: large_video.mp4",
  "timestamp": "2024-08-21T09:19:44Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `event` | `enum` | `connected` \| `progress` \| `completed` \| `failed` |
| `job_id` | `string` | Job identifier |
| `progress_pct` | `integer` | 0–100 |
| `assets_processed` | `integer` | Assets done so far |
| `assets_total` | `integer` | Total assets in job |
| `current_file` | `string \| null` | File currently being processed |
| `error_message` | `string \| null` | Only on `failed` event |
| `timestamp` | `string` | ISO 8601 UTC |

---

## 9. Shared Enums & Types

```
MediaType     : "video" | "image" | "audio"
JobStatus     : "queued" | "processing" | "done" | "failed"
WhisperModel  : "tiny" | "base" | "small" | "medium" | "large"
SortOrder     : "asc" | "desc"
AssetSortBy   : "ingested_at" | "file_name" | "duration_sec"
WebSocketEvent: "connected" | "progress" | "completed" | "failed"
```

---

## 10. Error Response Schema

All error responses follow this unified shape:

```json
{
  "error": {
    "code": "ASSET_NOT_FOUND",
    "message": "Asset with ID 'vid-9999' does not exist.",
    "detail": null
  }
}
```

| HTTP Status | Error Code | Trigger |
|-------------|------------|---------|
| `400` | `INVALID_REQUEST` | Malformed request body or missing required fields |
| `404` | `ASSET_NOT_FOUND` | `asset_id` does not exist |
| `404` | `JOB_NOT_FOUND` | `job_id` does not exist |
| `422` | `VALIDATION_ERROR` | Pydantic validation failure (auto-generated by FastAPI) |
| `500` | `PIPELINE_ERROR` | AI pipeline internal failure |
| `503` | `SERVICE_UNAVAILABLE` | ChromaDB or PostgreSQL unreachable |

---

## Changelog

| Version | Date | Author | Notes |
|---------|------|--------|-------|
| `v0.0.1-data-contract` | 2024-08-21 | Team | Initial contract — all 5 endpoints + WebSocket |
| `v0.0.2-data-contract` | 2026-06-18 | Team | Added Re-Ingest, Regenerate Insights, and In-Video Search filters |
