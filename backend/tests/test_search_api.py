import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from api.routes.search import get_embedder, get_vector_store
from schemas.search import SearchResponse

# Mock TextEmbedder
class MockTextEmbedder:
    async def embed(self, text: str) -> list[float]:
        # Return a dummy vector of length 1024
        return [0.1] * 1024

# Mock VectorStore
class MockVectorStore:
    def search(self, query_embedding: list[float], top_k: int = 10, filters: dict = None) -> list[dict]:
        # Return dummy search results that match our docs/api-contract.json schema expectation
        return [
            {
                "id": "emb-vid0042-s3",
                "score": 0.94,
                "metadata": {
                    "asset_id": "vid-0042",
                    "file_name": "vacation_reel_2024.mp4",
                    "media_type": "video",
                    "file_path": "/app/data/media/vacation_reel_2024.mp4",
                    "thumbnail_url": "/thumbnails/vid-0042-scene3.jpg",
                    "scene_index": 3,
                    "timestamp_start_sec": 142.5,
                    "timestamp_end_sec": 161.0,
                    "caption": "A person walks along a sandy beach at golden hour.",
                    "transcript_snippet": "This was the most peaceful evening.",
                    "tags": ["beach", "golden hour", "walking", "outdoors"]
                }
            }
        ]

@pytest.fixture
def override_dependencies():
    app.dependency_overrides[get_embedder] = lambda: MockTextEmbedder()
    app.dependency_overrides[get_vector_store] = lambda: MockVectorStore()
    yield
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_search_api_success(override_dependencies):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/search",
            json={
                "query": "person walking on a beach at sunset",
                "filters": {
                    "media_type": ["video"],
                    "tags": ["beach"]
                },
                "top_k": 5
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate against SearchResponse schema to ensure contract conformity
    SearchResponse(**data)
    
    assert data["query"] == "person walking on a beach at sunset"
    assert data["total_results"] == 1
    
    result = data["results"][0]
    assert result["asset_id"] == "vid-0042"
    assert result["score"] == 0.94
    assert result["media_type"] == "video"
    
    scene = result["scene"]
    assert scene["timestamp_start_sec"] == 142.5
    assert scene["timestamp_end_sec"] == 161.0
    assert scene["caption"] == "A person walks along a sandy beach at golden hour."
    assert scene["transcript_snippet"] == "This was the most peaceful evening."

@pytest.mark.asyncio
async def test_search_api_validation_error(override_dependencies):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/search",
            json={
                # Missing required 'query'
                "top_k": 5
            }
        )
    
    # Unprocessable Entity
    assert response.status_code == 422
