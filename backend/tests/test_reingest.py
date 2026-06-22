import pytest
import uuid
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

from database import Base
from models.asset import Asset
from models.scene import Scene
from models.ingest_job import IngestJob
from schemas.ingest import IngestOptions
from services.ingest_service import run_reingest_pipeline, run_regenerate_insights_job

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="function")
async def async_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine):
    async_session_maker = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session

# Create an async fixture to seed some initial data
@pytest_asyncio.fixture
async def seed_data(db_session: AsyncSession):
    asset_id = uuid.uuid4()
    job_id = uuid.uuid4()
    
    # 1. Create a job tracker
    job = IngestJob(
        job_id=job_id,
        status="completed",
        progress=100.0,
    )
    db_session.add(job)
    
    # 2. Create an asset
    asset = Asset(
        id=asset_id,
        file_name="test_video.mp4",
        file_path="uploads/test_video.mp4",
        media_type="video",
        full_transcript="This is a test video transcript.",
        summary="Old Summary",
        duration_sec=10.0
    )
    db_session.add(asset)
    
    # 3. Create old scenes
    scene1 = Scene(
        id=uuid.uuid4(),
        asset_id=asset_id,
        scene_index=1,
        timestamp_start_sec=0.0,
        timestamp_end_sec=5.0,
        caption="A beautiful sunrise",
        transcript_snippet="This is"
    )
    db_session.add(scene1)
    
    await db_session.commit()
    
    return {"asset_id": str(asset_id), "job_id": str(job_id)}

@pytest.mark.asyncio
async def test_reingest_atomic_swap_failure(db_session: AsyncSession, seed_data: dict, mocker):
    """
    Test that if the pipeline fails, the old DB scenes and vectors are not deleted.
    """
    asset_id = seed_data["asset_id"]
    new_job_id = str(uuid.uuid4())
    
    # 1. Add new job
    new_job = IngestJob(job_id=uuid.UUID(new_job_id), status="processing", progress=0.0)
    db_session.add(new_job)
    await db_session.commit()

    # 2. Mock storage service and pipeline to trigger an Exception BEFORE swap
    mocker.patch("services.ingest_service.publish_job_progress", return_value=None)
    mocker.patch("services.ingest_service.storage_service.client.download_file", return_value=True)
    mocker.patch("services.ingest_service.Path.mkdir", return_value=None)
    
    # Mock video pipeline to throw an error
    mocker.patch(
        "services.ingest_service.VideoAnalysisPipeline.analyze_video",
        side_effect=RuntimeError("Simulated pipeline failure")
    )
    
    # 3. Run Re-ingest
    options = IngestOptions(processing_mode="fast")
    await run_reingest_pipeline(new_job_id, asset_id, options)
    
    # 4. Verify old data remains intact because pipeline failed
    result = await db_session.execute(select(Scene).where(Scene.asset_id == uuid.UUID(asset_id)))
    scenes = result.scalars().all()
    assert len(scenes) == 1
    assert scenes[0].caption == "A beautiful sunrise"

    # Verify job status is failed
    job_result = await db_session.execute(select(IngestJob).where(IngestJob.job_id == uuid.UUID(new_job_id)))
    job = job_result.scalar_one()
    assert job.status == "failed"
    assert "Simulated pipeline failure" in job.error_message


@pytest.mark.asyncio
async def test_regenerate_insights(db_session: AsyncSession, seed_data: dict, mocker):
    """
    Test that regenerate insights job fetches scenes and updates the asset with new AI Insights.
    """
    asset_id = seed_data["asset_id"]
    new_job_id = str(uuid.uuid4())
    
    # 1. Add new job
    new_job = IngestJob(job_id=uuid.UUID(new_job_id), status="processing", progress=0.0)
    db_session.add(new_job)
    await db_session.commit()

    # 2. Mock RefinementLLM and publish_job_progress
    mocker.patch("services.ingest_service.publish_job_progress", return_value=None)
    class MockLLM:
        def generate_asset_insights(self, text):
            return {
                "summary": "MOCKED AI SUMMARY",
                "moods": ["happy", "mocked"],
                "objects": ["sun"],
                "best_for": ["testing"]
            }
    
    mocker.patch("services.ingest_service.create_refinement_llm", return_value=MockLLM())
    
    # 3. Run regenerate insights
    await run_regenerate_insights_job(new_job_id, asset_id)
    
    # 4. Refresh asset from DB and verify fields are updated
    asset = await db_session.get(Asset, uuid.UUID(asset_id))
    assert asset.summary == "MOCKED AI SUMMARY"
    assert asset.moods == ["happy", "mocked"]
    assert asset.objects == ["sun"]
    assert asset.best_for == ["testing"]

    # Verify job is completed
    job_result = await db_session.execute(select(IngestJob).where(IngestJob.job_id == uuid.UUID(new_job_id)))
    job = job_result.scalar_one()
    assert job.status == "completed"
    assert job.progress == 100.0
