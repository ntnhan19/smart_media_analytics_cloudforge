import pytest_asyncio
import pytest
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from database import Base
from models.asset import Asset
from models.scene import Scene
from models.ingest_job import IngestJob

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
async def async_session(async_engine):
    async_session_maker = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session

@pytest.mark.asyncio
async def test_create_and_query_asset(async_session):
    asset = Asset(
        file_name="test_video.mp4",
        file_path="/media/test_video.mp4",
        media_type="video",
        duration_sec=120.5,
        resolution="1920x1080",
        file_size_bytes=1024000,
        tags={"genre": "action"}
    )
    async_session.add(asset)
    await async_session.commit()

    # Query back
    result = await async_session.execute(select(Asset).filter_by(file_name="test_video.mp4"))
    fetched_asset = result.scalars().first()

    assert fetched_asset is not None
    assert fetched_asset.id == asset.id
    assert fetched_asset.duration_sec == 120.5
    assert fetched_asset.tags == {"genre": "action"}

@pytest.mark.asyncio
async def test_create_scene_with_foreign_key(async_session):
    asset = Asset(
        file_name="video2.mp4",
        file_path="/media/video2.mp4",
    )
    async_session.add(asset)
    await async_session.commit()

    scene = Scene(
        asset_id=asset.id,
        scene_index=1,
        timestamp_start_sec=0.0,
        timestamp_end_sec=10.0,
        caption="Introduction",
    )
    async_session.add(scene)
    await async_session.commit()

    # Query scene
    result = await async_session.execute(select(Scene).filter_by(asset_id=asset.id))
    fetched_scene = result.scalars().first()

    assert fetched_scene is not None
    assert fetched_scene.scene_index == 1
    assert fetched_scene.caption == "Introduction"

@pytest.mark.asyncio
async def test_unique_constraint_scene(async_session):
    asset = Asset(
        file_name="video3.mp4",
        file_path="/media/video3.mp4",
    )
    async_session.add(asset)
    await async_session.commit()

    scene1 = Scene(
        asset_id=asset.id,
        scene_index=1,
        timestamp_start_sec=0.0,
        timestamp_end_sec=5.0,
    )
    async_session.add(scene1)
    await async_session.commit()

    # Create scene with same index
    scene2 = Scene(
        asset_id=asset.id,
        scene_index=1,
        timestamp_start_sec=5.0,
        timestamp_end_sec=10.0,
    )
    async_session.add(scene2)
    with pytest.raises(IntegrityError):
        await async_session.commit()
