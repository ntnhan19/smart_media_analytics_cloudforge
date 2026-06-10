"""
Unit Tests — VectorDBClient (ChromaDB integration)

Run:
    pytest ai_pipeline/tests/test_vector_store.py -v

Requirements:
    pip install chromadb pytest
"""

import pytest
import random
import uuid
from typing import List

import chromadb

from ai_pipeline.database.vectordb_client import (
    VectorDBClient,
    VectorDBConfig,
    SceneSearchResult,
    VECTOR_DIM,
    SCENE_COLLECTION_NAME,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _rand_embedding(seed: int = 42) -> List[float]:
    """Return a reproducible 1024-dim unit-ish float vector."""
    rng = random.Random(seed)
    vec = [rng.gauss(0, 1) for _ in range(VECTOR_DIM)]
    norm = sum(v ** 2 for v in vec) ** 0.5
    return [v / norm for v in vec]


def _make_client() -> VectorDBClient:
    """Create an in-memory VectorDBClient (no disk I/O)."""
    chroma = chromadb.EphemeralClient()
    col_name = f"test_{uuid.uuid4().hex}"
    collection = chroma.get_or_create_collection(
        name=col_name,
        metadata={"hnsw:space": "cosine"},
    )
    client = object.__new__(VectorDBClient)
    client.config = VectorDBConfig(collection_name=col_name)
    client._client = chroma
    client._collection = collection
    return client


SAMPLE_SCENE = dict(
    asset_id="vid_20240101_abc123",
    file_name="beach_sunset.mp4",
    media_type="video/mp4",
    file_path="/videos/beach_sunset.mp4",
    scene_index=0,
    timestamp_start_sec=0.0,
    timestamp_end_sec=12.5,
    caption="A person walking along a sunset beach with gentle waves",
    transcript_snippet="The evening light painted the shore in warm golden hues.",
    thumbnail_url="https://cdn.example.com/thumb_scene0.jpg",
    tags=["sunset", "beach", "walking", "golden hour"],
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client() -> VectorDBClient:
    return _make_client()


@pytest.fixture
def client_with_scene(client: VectorDBClient) -> VectorDBClient:
    """Client pre-loaded with one scene."""
    embedding = _rand_embedding(seed=1)
    ok = client.upsert_scene(embedding=embedding, **SAMPLE_SCENE)
    assert ok, "Pre-condition: upsert must succeed"
    return client


# ── Tests: upsert_scene ───────────────────────────────────────────────────────

class TestUpsertScene:

    def test_upsert_returns_true(self, client):
        ok = client.upsert_scene(embedding=_rand_embedding(), **SAMPLE_SCENE)
        assert ok is True

    def test_upsert_stores_one_record(self, client_with_scene):
        assert client_with_scene.count() == 1

    def test_upsert_idempotent_no_duplicate(self, client):
        """Calling upsert twice on the same scene must NOT create a duplicate."""
        emb = _rand_embedding(seed=5)
        client.upsert_scene(embedding=emb, **SAMPLE_SCENE)
        client.upsert_scene(embedding=emb, **SAMPLE_SCENE)
        assert client.count() == 1

    def test_upsert_updates_embedding_on_second_call(self, client):
        """Second upsert with a different embedding should replace the first."""
        client.upsert_scene(embedding=_rand_embedding(seed=10), **SAMPLE_SCENE)
        new_emb = _rand_embedding(seed=99)
        client.upsert_scene(embedding=new_emb, **SAMPLE_SCENE)
        assert client.count() == 1

    def test_upsert_multiple_scenes_same_video(self, client):
        for i in range(5):
            scene = {**SAMPLE_SCENE, "scene_index": i}
            ok = client.upsert_scene(embedding=_rand_embedding(seed=i), **scene)
            assert ok is True
        assert client.count() == 5

    def test_upsert_scene_id_format(self, client):
        """ID must be {asset_id}_scene_{scene_index:04d}."""
        client.upsert_scene(embedding=_rand_embedding(), **{**SAMPLE_SCENE, "scene_index": 3})
        result = client.get(ids=[f"{SAMPLE_SCENE['asset_id']}_scene_0003"])
        assert len(result["ids"]) == 1

    def test_upsert_rejects_wrong_dim(self, client):
        bad_emb = [0.1] * 512  # wrong dimension
        ok = client.upsert_scene(embedding=bad_emb, **SAMPLE_SCENE)
        assert ok is False

    def test_upsert_tags_stored_as_csv(self, client):
        client.upsert_scene(embedding=_rand_embedding(), **SAMPLE_SCENE)
        raw = client.get(ids=[f"{SAMPLE_SCENE['asset_id']}_scene_0000"])
        meta = raw["metadatas"][0]
        assert meta["tags"] == "sunset,beach,walking,golden hour"

    def test_upsert_none_tags_stored_as_empty_string(self, client):
        scene = {**SAMPLE_SCENE, "tags": None}
        client.upsert_scene(embedding=_rand_embedding(), **scene)
        raw = client.get(ids=[f"{SAMPLE_SCENE['asset_id']}_scene_0000"])
        assert raw["metadatas"][0]["tags"] == ""

    def test_upsert_none_transcript_stored_as_empty_string(self, client):
        scene = {**SAMPLE_SCENE, "transcript_snippet": None}
        client.upsert_scene(embedding=_rand_embedding(), **scene)
        raw = client.get(ids=[f"{SAMPLE_SCENE['asset_id']}_scene_0000"])
        assert raw["metadatas"][0]["transcript_snippet"] == ""

    def test_upsert_document_content_is_combined(self, client):
        """Document must be the concatenation of caption and transcript_snippet."""
        client.upsert_scene(embedding=_rand_embedding(), **SAMPLE_SCENE)
        raw = client.get(ids=[f"{SAMPLE_SCENE['asset_id']}_scene_0000"])
        doc = raw["documents"][0]
        expected_doc = f"{SAMPLE_SCENE['caption']}. {SAMPLE_SCENE['transcript_snippet']}"
        assert doc == expected_doc


# ── Tests: query_scenes ───────────────────────────────────────────────────────

class TestQueryScenes:

    def test_query_returns_list(self, client_with_scene):
        results = client_with_scene.query_scenes(_rand_embedding(seed=1))
        assert isinstance(results, list)

    def test_query_returns_scene_search_result_objects(self, client_with_scene):
        results = client_with_scene.query_scenes(_rand_embedding(seed=1))
        assert all(isinstance(r, SceneSearchResult) for r in results)

    def test_query_score_in_valid_range(self, client_with_scene):
        """Cosine similarity score must be in [0, 1]."""
        results = client_with_scene.query_scenes(_rand_embedding(seed=1))
        for r in results:
            assert 0.0 <= r.score <= 1.0, f"score {r.score} out of range"

    def test_query_identical_embedding_returns_high_score(self, client):
        """Querying with the exact stored embedding should yield score ≈ 1.0."""
        emb = _rand_embedding(seed=42)
        client.upsert_scene(embedding=emb, **SAMPLE_SCENE)
        results = client.query_scenes(emb, n_results=1)
        assert len(results) == 1
        assert results[0].score >= 0.99, f"Expected score ≈ 1.0, got {results[0].score}"

    def test_query_sunset_beach_walking(self, client):
        """
        Semantic smoke-test: a beach/sunset query should surface the
        beach_sunset scene above an unrelated indoor scene.
        """
        beach_emb = _rand_embedding(seed=1)
        indoor_emb = _rand_embedding(seed=999)   # unrelated

        client.upsert_scene(embedding=beach_emb, **SAMPLE_SCENE)
        client.upsert_scene(embedding=indoor_emb, **{
            **SAMPLE_SCENE,
            "asset_id": "vid_indoor",
            "file_name": "office_meeting.mp4",
            "scene_index": 0,
            "caption": "People sitting around a conference table indoors",
            "tags": ["office", "meeting", "indoor"],
        })

        # Query with a vector close to the beach scene
        query_emb = [v + random.gauss(0, 0.01) for v in beach_emb]
        # Re-normalise
        norm = sum(v ** 2 for v in query_emb) ** 0.5
        query_emb = [v / norm for v in query_emb]

        results = client.query_scenes(query_emb, n_results=2)
        assert len(results) == 2
        # Beach scene should rank first (higher score)
        assert results[0].asset_id == SAMPLE_SCENE["asset_id"]

    def test_query_tags_deserialized_to_list(self, client_with_scene):
        results = client_with_scene.query_scenes(_rand_embedding(seed=1))
        assert results[0].tags == ["sunset", "beach", "walking", "golden hour"]

    def test_query_empty_tags_returns_empty_list(self, client):
        scene = {**SAMPLE_SCENE, "tags": []}
        client.upsert_scene(embedding=_rand_embedding(), **scene)
        results = client.query_scenes(_rand_embedding(), n_results=1)
        assert results[0].tags == []

    def test_query_metadata_fields_populated(self, client_with_scene):
        r = client_with_scene.query_scenes(_rand_embedding(seed=1))[0]
        assert r.asset_id == SAMPLE_SCENE["asset_id"]
        assert r.file_name == SAMPLE_SCENE["file_name"]
        assert r.media_type == SAMPLE_SCENE["media_type"]
        assert r.file_path == SAMPLE_SCENE["file_path"]
        assert r.scene_index == SAMPLE_SCENE["scene_index"]
        assert r.timestamp_start_sec == SAMPLE_SCENE["timestamp_start_sec"]
        assert r.timestamp_end_sec == SAMPLE_SCENE["timestamp_end_sec"]
        assert r.caption == SAMPLE_SCENE["caption"]

    def test_query_thumbnail_url_preserved(self, client_with_scene):
        r = client_with_scene.query_scenes(_rand_embedding(seed=1))[0]
        assert r.thumbnail_url == SAMPLE_SCENE["thumbnail_url"]

    def test_query_empty_thumbnail_returns_none(self, client):
        scene = {**SAMPLE_SCENE, "thumbnail_url": None}
        client.upsert_scene(embedding=_rand_embedding(), **scene)
        r = client.query_scenes(_rand_embedding(), n_results=1)[0]
        assert r.thumbnail_url is None

    def test_query_filter_by_asset_id(self, client):
        """asset_id filter must exclude other videos."""
        client.upsert_scene(embedding=_rand_embedding(seed=1), **SAMPLE_SCENE)
        client.upsert_scene(embedding=_rand_embedding(seed=2), **{
            **SAMPLE_SCENE,
            "asset_id": "vid_other",
            "scene_index": 0,
        })
        results = client.query_scenes(
            _rand_embedding(seed=1),
            n_results=10,
            asset_id=SAMPLE_SCENE["asset_id"],
        )
        assert all(r.asset_id == SAMPLE_SCENE["asset_id"] for r in results)
        assert len(results) == 1

    def test_query_wrong_dim_returns_empty(self, client_with_scene):
        results = client_with_scene.query_scenes([0.1] * 512)
        assert results == []

    def test_query_n_results_respected(self, client):
        for i in range(10):
            client.upsert_scene(embedding=_rand_embedding(seed=i), **{**SAMPLE_SCENE, "scene_index": i})
        results = client.query_scenes(_rand_embedding(), n_results=3)
        assert len(results) <= 3


# ── Tests: delete_by_video_id ─────────────────────────────────────────────────

class TestDeleteByVideoId:

    def test_delete_removes_all_scenes_for_video(self, client):
        for i in range(4):
            client.upsert_scene(embedding=_rand_embedding(seed=i), **{**SAMPLE_SCENE, "scene_index": i})
        assert client.count() == 4

        ok = client.delete_by_video_id(SAMPLE_SCENE["asset_id"])
        assert ok is True
        assert client.count() == 0

    def test_delete_only_removes_target_video(self, client):
        """Scenes from other videos must survive the delete."""
        for i in range(3):
            client.upsert_scene(embedding=_rand_embedding(seed=i), **{**SAMPLE_SCENE, "scene_index": i})
        other_scene = {**SAMPLE_SCENE, "asset_id": "vid_keep_me", "scene_index": 0}
        client.upsert_scene(embedding=_rand_embedding(seed=99), **other_scene)
        assert client.count() == 4

        client.delete_by_video_id(SAMPLE_SCENE["asset_id"])
        assert client.count() == 1

        remaining = client.get(where={"asset_id": {"$eq": "vid_keep_me"}})
        assert len(remaining["ids"]) == 1

    def test_delete_nonexistent_video_returns_true(self, client):
        """Deleting a video that doesn't exist should not raise — return True."""
        ok = client.delete_by_video_id("ghost_video_id")
        assert ok is True

    def test_delete_then_reingest(self, client):
        """After deleting, re-upserting should work cleanly."""
        emb = _rand_embedding(seed=7)
        client.upsert_scene(embedding=emb, **SAMPLE_SCENE)
        client.delete_by_video_id(SAMPLE_SCENE["asset_id"])
        assert client.count() == 0

        ok = client.upsert_scene(embedding=emb, **SAMPLE_SCENE)
        assert ok is True
        assert client.count() == 1


# ── Tests: SceneSearchResult dataclass ───────────────────────────────────────

class TestSceneSearchResultDataclass:

    def test_all_fields_present(self):
        r = SceneSearchResult(
            asset_id="a", file_name="f", media_type="video/mp4",
            file_path="/p", thumbnail_url=None, score=0.9,
            scene_index=0, timestamp_start_sec=0.0, timestamp_end_sec=5.0,
            caption="cap", transcript_snippet=None, tags=["x"],
        )
        assert r.score == 0.9
        assert r.tags == ["x"]
        assert r.thumbnail_url is None
        assert r.transcript_snippet is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
