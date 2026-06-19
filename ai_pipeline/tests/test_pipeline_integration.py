import asyncio
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest


pytestmark = pytest.mark.integration

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
for path in (PROJECT_ROOT, BACKEND_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://echoscene:echoscene_dev_password@localhost:5433/echoscene",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("MINIO_ROOT_USER", "echoscene")
os.environ.setdefault("MINIO_ROOT_PASSWORD", "echoscene_dev_password")
os.environ.setdefault("MINIO_BUCKET_MEDIA", "media")
os.environ.setdefault("AI_PROVIDER", "local")
os.environ.setdefault("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
os.environ.setdefault("EMBEDDING_MODEL", "bge-m3:latest")
os.environ.setdefault("QWEN_VL_MODEL", "qwen2.5vl:3b")
os.environ.setdefault("EMBEDDING_DIM", "1024")


@pytest.fixture(scope="session")
def integration_enabled():
    if os.getenv("RUN_PIPELINE_INTEGRATION") != "1":
        pytest.skip("Set RUN_PIPELINE_INTEGRATION=1 to run the Docker Compose smoke test")


@pytest.fixture()
def sample_video(tmp_path, integration_enabled):
    video_path = tmp_path / "smoke.mp4"
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        "testsrc=size=320x240:rate=15:duration=3",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=1000:duration=3",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        "-y",
        str(video_path),
    ]
    subprocess.run(cmd, check=True)
    return video_path


@pytest.mark.asyncio
async def test_pipeline_e2e_smoke(sample_video, integration_enabled):
    from sqlalchemy import select, text

    from database import Base, SessionLocal, engine
    from models.asset import Asset
    from models.ingest_job import IngestJob
    from models.scene import Scene
    from services.ingest_service import run_ingest_pipeline
    from services.storage_service import storage_service

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    job_id = uuid.uuid4()
    async with SessionLocal() as db:
        db.add(IngestJob(job_id=job_id, status="queued", progress=0.0))
        await db.commit()

    progress_events = []

    async def listen_for_progress():
        import redis.asyncio as redis

        client = redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
        pubsub = client.pubsub()
        await pubsub.subscribe(f"job_{job_id}")
        try:
            async for message in pubsub.listen():
                if message.get("type") == "message":
                    progress_events.append(message["data"])
                    if '"status": "completed"' in message["data"]:
                        break
        finally:
            await pubsub.unsubscribe(f"job_{job_id}")
            await pubsub.close()
            await client.close()

    listener_task = asyncio.create_task(listen_for_progress())
    await asyncio.sleep(0.2)

    await run_ingest_pipeline(
        job_id_str=str(job_id),
        source_path=str(sample_video),
        options=None,
    )

    await asyncio.wait_for(listener_task, timeout=10)

    async with SessionLocal() as db:
        job = await db.get(IngestJob, job_id)
        assert job.status == "completed"
        assert job.progress == 100.0

        asset_result = await db.execute(select(Asset).where(Asset.file_name == sample_video.name))
        asset = asset_result.scalars().first()
        assert asset is not None
        assert asset.duration_sec and asset.duration_sec > 0
        assert asset.resolution
        assert asset.file_size_bytes > 0
        assert isinstance(asset.tags, list)

        scene_result = await db.execute(select(Scene).where(Scene.asset_id == asset.id))
        scenes = scene_result.scalars().all()
        assert scenes
        assert scenes[0].caption
        assert scenes[0].keyframe_s3_key == f"keyframes/{asset.id}/0.jpg"
        assert scenes[0].embedding is not None
        assert len(scenes[0].embedding) == 1024

        assert storage_service.client.file_exists(scenes[0].keyframe_s3_key)

    assert progress_events
    assert any('"current_step": "embedding"' in event for event in progress_events)
    assert any('"status": "completed"' in event for event in progress_events)
