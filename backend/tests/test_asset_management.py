import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import uuid

# We mock the database and vector store before importing the app
# to prevent actual DB connections in this simple test.
from main import app

client = TestClient(app)

@pytest.fixture
def mock_db():
    with patch("api.routes.assets.get_db") as mock_get_db_assets, \
         patch("api.routes.scenes.get_db") as mock_get_db_scenes, \
         patch("api.routes.media.get_db") as mock_get_db_media:
        
        mock_session = AsyncMock()
        mock_get_db_assets.return_value = mock_session
        mock_get_db_scenes.return_value = mock_session
        mock_get_db_media.return_value = mock_session
        yield mock_session

@pytest.fixture
def mock_vector_store():
    with patch("api.routes.assets.get_vector_store") as m1, \
         patch("api.routes.scenes.get_vector_store") as m2:
        mock_store = MagicMock()
        # Ensure async methods are mockable if they are coroutines
        mock_store.delete_by_asset = AsyncMock()
        mock_store.update_embedding = AsyncMock()
        
        m1.return_value = mock_store
        m2.return_value = mock_store
        yield mock_store

@pytest.fixture
def mock_storage():
    with patch("api.routes.assets.storage_service") as m1, \
         patch("api.routes.media.storage_service") as m2:
        m1.delete_asset_files = AsyncMock(return_value=True)
        m2.get_stream_url.return_value = "http://localhost:8000/mock/stream"
        yield m1

def test_get_assets(mock_db):
    response = client.get("/api/v1/assets?limit=10&offset=0")
    # For now, it will hit the DB which is mocked, but TestClient 
    # uses dependency overrides better. Let's use app.dependency_overrides
    pass

# We should use app.dependency_overrides to properly mock db
@pytest.fixture
def override_db():
    mock_session = AsyncMock()
    from database import get_db
    app.dependency_overrides[get_db] = lambda: mock_session
    yield mock_session
    app.dependency_overrides.clear()

def test_get_assets_with_override(override_db):
    mock_result = MagicMock()
    
    mock_asset = MagicMock()
    mock_asset.id = uuid.uuid4()
    mock_asset.file_name = "test.mp4"
    mock_asset.file_size_bytes = 1000
    mock_asset.duration_sec = 60.0
    mock_asset.status = "ready"
    mock_asset.ingested_at = "2026-01-01T00:00:00Z"
    
    mock_result.scalars.return_value.all.return_value = [mock_asset]
    override_db.execute.return_value = mock_result
    
    response = client.get("/api/v1/assets")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["file_name"] == "test.mp4"

def test_delete_asset(override_db, mock_vector_store, mock_storage):
    mock_asset = MagicMock()
    mock_asset.id = uuid.uuid4()
    mock_asset.file_path = "uploads/test.mp4"
    override_db.get.return_value = mock_asset
    
    mock_scene_result = MagicMock()
    mock_scene = MagicMock()
    mock_scene.keyframe_s3_key = "keyframes/test/1.jpg"
    mock_scene_result.scalars.return_value.all.return_value = [mock_scene]
    override_db.execute.return_value = mock_scene_result
    
    asset_id_str = str(mock_asset.id)
    response = client.delete(f"/api/v1/assets/{asset_id_str}")
    
    assert response.status_code == 204
    mock_vector_store.delete_by_asset.assert_called_once_with(asset_id_str)
    mock_storage.delete_asset_files.assert_called_once_with(asset_id_str, "uploads/test.mp4", ["keyframes/test/1.jpg"])
    override_db.delete.assert_called_once_with(mock_asset)
    override_db.commit.assert_called_once()

@patch("api.routes.scenes.embedder")
def test_patch_scene(mock_embedder, override_db, mock_vector_store):
    mock_embedder.embed = AsyncMock(return_value=[0.1, 0.2])
    
    mock_scene = MagicMock()
    mock_scene.id = uuid.uuid4()
    mock_scene.asset_id = uuid.uuid4()
    mock_scene.scene_index = 1
    mock_scene.timestamp_start_sec = 0.0
    mock_scene.timestamp_end_sec = 5.0
    mock_scene.caption = "Old caption"
    mock_scene.transcript_snippet = "Old transcript"
    mock_scene.keyframe_s3_key = "test.jpg"
    
    override_db.get.return_value = mock_scene
    
    scene_id_str = str(mock_scene.id)
    response = client.patch(
        f"/api/v1/scenes/{scene_id_str}",
        json={"caption": "New caption", "transcript": "New transcript"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["caption"] == "New caption"
    assert data["transcript_snippet"] == "New transcript"
    
    # Verify embedding updated
    mock_embedder.embed.assert_called_once_with("New caption New transcript")
    mock_vector_store.update_embedding.assert_called_once_with(
        scene_id_str, 
        [0.1, 0.2], 
        metadata_updates={"caption": "New caption", "transcript_snippet": "New transcript"}
    )
    override_db.commit.assert_called_once()

def test_get_media_stream(override_db, mock_storage):
    mock_asset = MagicMock()
    mock_asset.id = uuid.uuid4()
    mock_asset.file_path = "uploads/video.mp4"
    override_db.get.return_value = mock_asset
    
    asset_id_str = str(mock_asset.id)
    response = client.get(f"/api/v1/media/stream/{asset_id_str}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["stream_url"] == "http://localhost:8000/mock/stream"
