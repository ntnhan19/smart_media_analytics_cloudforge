import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import uuid
import json
from unittest.mock import patch, MagicMock, AsyncMock
from schemas.search import SearchRequest, SearchRequestFilters
from schemas.ingest import IngestRequest, IngestOptions
from models.ingest_job import IngestJob
from models.asset import Asset
from sqlalchemy import select
from fastapi.testclient import TestClient
import time

from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_part1_asset_id_saved_to_ingest_job_and_websocket():
    """
    Test that asset_id is saved to IngestJob when asset is created
    and that asset_id is included in the WebSocket payload.
    """
    job_id_str = str(uuid.uuid4())
    asset_id_str = str(uuid.uuid4())
    
    # Mock AsyncSession
    mock_session = AsyncMock()
    mock_job = MagicMock()
    mock_job.job_id = uuid.UUID(job_id_str)
    mock_job.asset_id = None
    mock_job.progress = 0.0
    mock_job.assets_queued = 1
    mock_job.assets_processed = 0
    mock_session.get.return_value = mock_job
    
    # Mock manager
    from services.ingest_service import publish_job_progress
    from core.websocket_manager import manager
    
    with patch.object(manager, 'publish_progress', new_callable=AsyncMock) as mock_publish:
        with patch('services.ingest_service.SessionLocal', return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock())):
            # Simulate updating job
            await publish_job_progress(
                job_id_str, "processing", 10.0, "testing", asset_id=asset_id_str, update_db=True
            )
            
            # Verify DB commit was called
            mock_session.commit.assert_called()
            
            # Verify job object was updated
            assert mock_job.asset_id == uuid.UUID(asset_id_str)
            
            # Verify websocket payload
            mock_publish.assert_called_once()
            payload = mock_publish.call_args[0][1]
            assert payload["asset_id"] == asset_id_str

@pytest.mark.asyncio
async def test_part3_in_video_search_asset_id_filter():
    """
    Test that search API applies asset_id filter.
    """
    # Create a mock vector store
    class MockVectorStore:
        async def search(self, query_embedding, n_results=10, filters=None):
            self.last_filters = filters
            return [
                {
                    "id": str(uuid.uuid4()),
                    "asset_id": "test-asset-id-123",
                    "scene_index": 0,
                    "timestamp_start_sec": 0.0,
                    "timestamp_end_sec": 5.0,
                    "caption": "test caption",
                    "file_name": "test.mp4"
                }
            ]
            
    mock_vs = MockVectorStore()
    
    class MockTextEmbedder:
        async def embed(self, text: str) -> list[float]:
            return [0.1] * 1024
            
    from api.routes.search import get_embedder, get_vector_store
    app.dependency_overrides[get_embedder] = lambda: MockTextEmbedder()
    app.dependency_overrides[get_vector_store] = lambda: mock_vs
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Request with asset_id
        response = await client.post(
            "/api/v1/search",
            json={
                "query": "test query",
                "filters": {"asset_id": "test-asset-id-123"},
                "top_k": 5
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["asset_id"] == "test-asset-id-123"
        
        # Verify that vector store search was called with correct filter
        assert hasattr(mock_vs, "last_filters")
        assert mock_vs.last_filters == {"asset_id": "test-asset-id-123"}
        
        # Request without asset_id
        response = await client.post(
            "/api/v1/search",
            json={
                "query": "test query",
                "top_k": 5
            }
        )
        assert response.status_code == 200
        assert mock_vs.last_filters is None

    app.dependency_overrides.clear()
