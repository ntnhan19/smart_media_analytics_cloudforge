"""
ingest_service.py
Background service xử lý ingest job hoàn chỉnh
- Cập nhật trạng thái Job + Asset
- Lưu Scenes + Embedding
- Publish Redis Pub/Sub realtime
- Hỗ trợ retry và error handling tốt
"""

import asyncio
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# AI Pipeline
from ai_pipeline.ingestion.contracts import VideoAnalysisContract
from ai_pipeline.ingestion.video_pipeline import VideoAnalysisPipeline

# Core & Database
try:
    from core.websocket_manager import manager
    from database import SessionLocal
except ImportError:  # Allows importing as backend.services.ingest_service from repo root.
    from backend.core.websocket_manager import manager
    from backend.database import SessionLocal

# Models
try:
    from models.asset import Asset
    from models.ingest_job import IngestJob
    from models.scene import Scene
except ImportError:  # Allows importing as backend.services.ingest_service from repo root.
    from backend.models.asset import Asset
    from backend.models.ingest_job import IngestJob
    from backend.models.scene import Scene

# Schemas & Services
try:
    from schemas.ingest import IngestOptions
    from services.storage_service import storage_service
except ImportError:  # Allows importing as backend.services.ingest_service from repo root.
    from backend.schemas.ingest import IngestOptions
    from backend.services.storage_service import storage_service

logger = logging.getLogger(__name__)

SUPPORTED_MEDIA_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv", ".webm", ".wav", ".mp3")


async def publish_job_progress(
    job_id_str: str,
    status: str,
    progress: float,
    current_step: str,
    error_message: Optional[str] = None,
) -> None:
    """Publish progress qua Redis/Websocket và cập nhật DB an toàn."""
    payload = {
        "job_id": job_id_str,
        "status": status,
        "progress": round(float(progress), 2),
        "current_step": current_step,
        "error_message": error_message,
    }

    # Publish realtime
    await manager.publish_progress(job_id_str, payload)

    # Update DB
    try:
        async with SessionLocal() as db:
            job = await db.get(IngestJob, uuid.UUID(job_id_str))
            if job:
                job.status = status
                job.progress = float(progress)
                if error_message:
                    job.error_message = error_message
                await db.commit()
    except Exception as e:
        logger.warning(f"Failed to update job progress in DB: {e}")


def _media_type_for(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return "audio" if suffix in {".wav", ".mp3"} else "video"


def _discover_files(source_path: str) -> List[str]:
    """Tìm tất cả file media hợp lệ."""
    if not source_path or not os.path.exists(source_path):
        return []

    path = Path(source_path)
    if path.is_file():
        return [str(path)] if str(path).lower().endswith(SUPPORTED_MEDIA_EXTENSIONS) else []
    
    # Directory
    return [
        str(f) for f in path.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_MEDIA_EXTENSIONS
    ]


async def _create_or_get_asset(
    db: AsyncSession,
    file_path: str,
    video_s3_key: str,
) -> Asset:
    """Tạo Asset mới hoặc lấy nếu đã tồn tại."""
    asset = Asset(
        id=uuid.uuid4(),
        file_name=Path(file_path).name,
        file_path=video_s3_key,
        media_type=_media_type_for(file_path),
        file_size_bytes=Path(file_path).stat().st_size if Path(file_path).exists() else 0,
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


async def _persist_analysis(
    db: AsyncSession,
    asset: Asset,
    analysis: VideoAnalysisContract,
) -> None:
    """Lưu toàn bộ kết quả phân tích vào DB."""
    # Update Asset
    asset.duration_sec = analysis.duration_sec
    asset.resolution = analysis.resolution
    asset.file_size_bytes = analysis.file_size_bytes
    asset.full_transcript = analysis.full_transcript or ""
    asset.tags = [tag.to_dict() for tag in analysis.tags]

    # Save Scenes
    for scene_data in analysis.scenes:
        scene = Scene(
            id=uuid.uuid4(),
            asset_id=asset.id,
            scene_index=scene_data.scene_index,
            timestamp_start_sec=scene_data.timestamp_start_sec,
            timestamp_end_sec=scene_data.timestamp_end_sec,
            caption=scene_data.caption,
            transcript_snippet=scene_data.transcript_snippet,
            searchable_text=scene_data.searchable_text,
            semantic_metadata=scene_data.semantic_metadata.to_dict() if hasattr(scene_data.semantic_metadata, "to_dict") else {},
            keyframe_s3_key=scene_data.keyframe_s3_key,
            embedding=scene_data.embedding,
            tags=[t.to_dict() for t in scene_data.tags],
        )
        db.add(scene)

    await db.commit()


async def _process_single_file(
    file_path: str,
    db: AsyncSession,
    options: IngestOptions,
    job_id_str: str,
) -> None:
    """Xử lý một file video."""
    filename = Path(file_path).name
    video_s3_key = f"uploads/{job_id_str}/{filename}"

    await publish_job_progress(job_id_str, "processing", 5.0, "uploading_file")

    # Upload to MinIO/S3
    if storage_service.client and os.path.exists(file_path):
        loop = asyncio.get_running_loop()
        success = await loop.run_in_executor(
            None, storage_service.client.upload_file, file_path, video_s3_key
        )
        if not success:
            raise RuntimeError(f"Upload failed: {video_s3_key}")

    # Create Asset
    asset = await _create_or_get_asset(db, file_path, video_s3_key)

    # Progress callback
    def progress_callback(step: str, progress: float):
        asyncio.create_task(
            publish_job_progress(job_id_str, "processing", progress, step)
        )

    # Run Pipeline
    loop = asyncio.get_running_loop()
    pipeline = VideoAnalysisPipeline(
        processing_mode=getattr(options, "processing_mode", "fast"),
        storage_client=storage_service.client,
        progress_callback=progress_callback,
    )

    analysis: VideoAnalysisContract = await loop.run_in_executor(
        None,
        lambda: pipeline.analyze_video(
            video_path=Path(file_path),
            asset_id=str(asset.id),
            source_storage_key=video_s3_key,
        )
    )

    await publish_job_progress(job_id_str, "processing", 95.0, "saving_to_database")
    await _persist_analysis(db, asset, analysis)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def run_ingest_pipeline(
    job_id_str: str,
    source_path: str,
    options: IngestOptions,
    is_retry: bool = False,
) -> None:
    """Main entry point cho ingest job."""
    logger.info(f"Starting ingest pipeline for job {job_id_str} | retry={is_retry}")

    async with SessionLocal() as db:
        job = await db.get(IngestJob, uuid.UUID(job_id_str))
        if not job:
            logger.error(f"Job {job_id_str} not found")
            return

        try:
            files = _discover_files(source_path)
            job.assets_queued = len(files)
            job.status = "processing"
            job.progress = 0.0
            await db.commit()

            await publish_job_progress(job_id_str, "processing", 0.0, "started")

            if not files:
                job.status = "completed"
                job.progress = 100.0
                await db.commit()
                await publish_job_progress(job_id_str, "completed", 100.0, "no_files")
                return

            for idx, file_path in enumerate(files, 1):
                await _process_single_file(file_path, db, options, job_id_str)
                job.assets_processed = idx
                job.progress = round((idx / len(files)) * 100, 2)
                await db.commit()

            job.status = "completed"
            job.progress = 100.0
            await db.commit()
            await publish_job_progress(job_id_str, "completed", 100.0, "completed")

        except Exception as exc:
            logger.exception(f"Pipeline failed for job {job_id_str}")
            job.status = "failed"
            job.error_message = str(exc)[:500]
            await db.commit()
            await publish_job_progress(
                job_id_str, "failed", job.progress or 0.0, "failed", str(exc)
            )
