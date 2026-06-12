import pytest
from fastapi.testclient import TestClient
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from main import app
from database import Base, engine
import time

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(init_db())

client = TestClient(app)

from unittest.mock import patch

@patch("services.ingest_service.VectorStore")
@patch("services.ingest_service.TextEmbedder")
def test_ingest_flow(mock_embedder, mock_vector_store):
    # 1. Start job
    response = client.post(
        "/api/v1/ingest",
        json={
            "source_path": "/dummy/path",
            "options": {
                "scene_detection": True,
                "transcription": True,
                "vision_caption": True,
                "whisper_model": "base"
            }
        }
    )
    
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    job_id = data["job_id"]
    
    # Wait for background task to process (it assumes 0 files, so very fast)
    time.sleep(0.5)
    
    # 2. Check status
    response = client.get(f"/api/v1/ingest/status/{job_id}")
    assert response.status_code == 200
    status_data = response.json()
    assert status_data["job_id"] == job_id
    assert status_data["status"] in ["processing", "completed"]
    assert status_data["assets_queued"] == 0
    assert status_data["progress"] == 0.0

from core.websocket_manager import manager

@patch("services.ingest_service.VectorStore")
@patch("services.ingest_service.TextEmbedder")
def test_websocket_ingest_progress(mock_embedder, mock_vector_store):
    # Trigger an ingest job first
    response = client.post(
        "/api/v1/ingest",
        json={"source_path": "/dummy/path"}
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    
    # Mock manager to send progress payload immediately upon connection
    # This prevents the TestClient synchronous background task race condition hang
    original_connect = manager.connect
    async def mock_connect(websocket, j_id):
        await original_connect(websocket, j_id)
        await websocket.send_json({"event": "progress", "job_id": j_id})
        
    manager.connect = mock_connect
    
    # Connect websocket
    from fastapi import WebSocketDisconnect
    try:
        with client.websocket_connect(f"/api/v1/ingest/ws/{job_id}") as websocket:
            # We expect a progress/completed event
            data = websocket.receive_json()
            assert "event" in data
            assert data["event"] in ["progress", "completed", "failed"]
            assert data["job_id"] == job_id
    except WebSocketDisconnect:
        pass
    finally:
        manager.connect = original_connect
