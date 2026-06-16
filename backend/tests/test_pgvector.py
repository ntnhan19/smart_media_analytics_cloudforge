import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from core.embeddings.pgvector_store import PGVectorStore

@pytest.mark.asyncio
async def test_pgvector_add_embeddings():
    adapter = PGVectorStore()
    
    with patch("core.embeddings.pgvector_store.SessionLocal") as mock_session:
        mock_db = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db
        
        # Mock scene object
        mock_scene = MagicMock()
        mock_db.get.return_value = mock_scene
        
        embeddings = [[0.1, 0.2, 0.3]]
        metadatas = [{"asset_id": "test"}]
        ids = ["00000000-0000-0000-0000-000000000000"]
        
        await adapter.add_embeddings(embeddings, metadatas, ids)
        
        mock_db.get.assert_called_once()
        assert mock_scene.embedding == [0.1, 0.2, 0.3]
        mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_pgvector_search():
    adapter = PGVectorStore()
    
    with patch("core.embeddings.pgvector_store.SessionLocal") as mock_session:
        mock_db = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db
        
        mock_result = MagicMock()
        mock_scene = MagicMock()
        mock_scene.id = "test-id"
        mock_scene.asset_id = "asset-id"
        mock_scene.scene_index = 1
        mock_scene.timestamp_start_sec = 0.0
        mock_scene.timestamp_end_sec = 5.0
        mock_scene.caption = "Test"
        mock_scene.transcript_snippet = ""
        mock_scene.keyframe_s3_key = ""
        
        mock_result.scalars.return_value.all.return_value = [mock_scene]
        mock_db.execute.return_value = mock_result
        
        results = await adapter.search([0.1, 0.2, 0.3], n_results=1)
        
        assert len(results) == 1
        assert results[0]["id"] == "test-id"
        mock_db.execute.assert_awaited_once()
