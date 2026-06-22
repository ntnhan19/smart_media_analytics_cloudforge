import asyncio
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai_pipeline.ingestion.contracts import VideoAnalysisContract
from ai_pipeline.ingestion.video_pipeline import VideoAnalysisPipeline
from core.websocket_manager import manager
from database import SessionLocal
from models.asset import Asset
from models.ingest_job import IngestJob
from models.scene import Scene
from schemas.ingest import IngestOptions
from services.storage_service import storage_service

logger = logging.getLogger(__name__)

SUPPORTED_MEDIA_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv", ".webm", ".wav", ".mp3")


async def publish_job_progress(
    job_id_str: str,
    status: str,
    progress: float,
    current_step: str,
    error_message: Optional[str] = None,
    update_db: bool = True,  # Thêm flag linh hoạt điều hướng ghi DB
) -> None:
    """Update ingest_jobs and publish the canonical Redis progress payload."""
    payload = {
        "job_id": job_id_str,
        "status": status,
        "progress": float(progress),
        "current_step": current_step,
        "error_message": error_message,
    }

    # Chỉ ghi DB ở luồng Async chính an toàn để tránh xung đột đa luồng
    if update_db:
        try:
            async with SessionLocal() as db:
                job = await db.get(IngestJob, uuid.UUID(job_id_str))
                if job:
                    job.status = status
                    job.progress = float(progress)
                    job.error_message = error_message
                    await db.commit()
        except Exception as db_err:
            logger.warning(f"DB progress update skipped to avoid deadlock: {db_err}")

    # Phát tín hiệu thời gian thực qua Redis Pub/Sub / Websocket
    await manager.publish_progress(job_id_str, payload)


def _media_type_for(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {".wav", ".mp3"}:
        return "audio"
    return "video"


def _discover_files(source_path: str) -> List[str]:
    if not source_path or not os.path.exists(source_path):
        return []
    if os.path.isdir(source_path):
        return [
            os.path.join(source_path, name)
            for name in os.listdir(source_path)
            if name.lower().endswith(SUPPORTED_MEDIA_EXTENSIONS)
        ]
    return [source_path] if source_path.lower().endswith(SUPPORTED_MEDIA_EXTENSIONS) else []


def _contract_tags_to_json(analysis: VideoAnalysisContract) -> List[Dict[str, Any]]:
    return [tag.to_dict() for tag in analysis.tags]


async def _persist_analysis(
    db: AsyncSession,
    asset: Asset,
    analysis: VideoAnalysisContract,
) -> None:
    asset.duration_sec = analysis.duration_sec
    asset.resolution = analysis.resolution
    asset.file_size_bytes = analysis.file_size_bytes
    asset.full_transcript = analysis.full_transcript
    asset.tags = _contract_tags_to_json(analysis)

    for scene_data in analysis.scenes:
        scene = Scene(
            id=uuid.uuid4(),
            asset_id=asset.id,
            scene_index=scene_data.scene_index,
            timestamp_start_sec=scene_data.timestamp_start_sec,
            timestamp_end_sec=scene_data.timestamp_end_sec,
            caption=scene_data.caption,
            transcript_snippet=scene_data.transcript_snippet,
            keyframe_path=scene_data.keyframe_path,
            keyframe_s3_key=scene_data.keyframe_s3_key,
            embedding=scene_data.embedding,
        )
        db.add(scene)

    await db.commit()


async def _create_asset(
    db: AsyncSession,
    file_path: str,
    video_s3_key: str,
) -> Asset:
    asset = Asset(
        id=uuid.uuid4(),
        file_name=os.path.basename(file_path),
        file_path=video_s3_key,
        media_type=_media_type_for(file_path),
        file_size_bytes=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


async def _process_single_file(
    file_path: str,
    db: AsyncSession,
    options: IngestOptions,
    job_id_str: str,
) -> None:
    filename = os.path.basename(file_path)
    await publish_job_progress(job_id_str, "processing", 5.0, "uploading_to_s3")

    video_s3_key = f"uploads/{job_id_str}/{filename}"
    if storage_service.client and os.path.exists(file_path):
        loop = asyncio.get_running_loop()
        ok = await loop.run_in_executor(
            None,
            storage_service.client.upload_file,
            file_path,
            video_s3_key,
        )
        if not ok:
            raise RuntimeError(f"Failed to upload source media to storage: {video_s3_key}")

    asset = await _create_asset(db, file_path, video_s3_key)
    loop = asyncio.get_running_loop()

    # TỐI ƯU CALLBACK: Chỉ bắn sự kiện tiến trình ra ngoài, không lock DB ngầm trong executor
    def progress_callback(current_step: str, progress: float) -> None:
        asyncio.run_coroutine_threadsafe(
            publish_job_progress(job_id_str, "processing", progress, current_step, update_db=False),
            loop,
        )

    def run_pipeline() -> VideoAnalysisContract:
        # Lấy chế độ xử lý động từ cấu hình options
        mode = getattr(options, "processing_mode", "fast") if options else "fast"
        pipeline = VideoAnalysisPipeline(
            processing_mode=mode,
            storage_client=storage_service.client,
            progress_callback=progress_callback,
        )
        return pipeline.analyze_video(
            video_path=Path(file_path),
            asset_id=str(asset.id),
            source_storage_key=video_s3_key,
        )

    analysis = await loop.run_in_executor(None, run_pipeline)
    
    # Commit đồng loạt toàn bộ dữ liệu sạch tại luồng chính Async
    await publish_job_progress(job_id_str, "processing", 96.0, "persisting_results")
    await _persist_analysis(db, asset, analysis)


async def run_ingest_pipeline(
    job_id_str: str,
    source_path: str,
    options: IngestOptions,
    is_retry: bool = False,
) -> None:
    """Background task to process ingest jobs asynchronously."""
    logger.info(f"Starting ingest pipeline for job_id: {job_id_str} (Retry: {is_retry})")

    async with SessionLocal() as db:
        job_id_uuid = uuid.UUID(job_id_str)
        result = await db.execute(select(IngestJob).where(IngestJob.job_id == job_id_uuid))
        job = result.scalar_one_or_none()
        if not job:
            logger.error(f"Job {job_id_str} not found in database.")
            return

        try:
            files_to_process = _discover_files(source_path)
            if is_retry and not files_to_process:
                raise FileNotFoundError("Retry requires the original source path to be supplied")

            job.assets_queued = len(files_to_process)
            job.assets_processed = 0
            job.status = "processing"
            job.progress = 0.0
            job.error_message = None
            await db.commit()
            
            await publish_job_progress(job_id_str, "processing", 0.0, "queued")

            if not files_to_process:
                job.status = "completed"
                job.progress = 100.0
                await db.commit()
                await publish_job_progress(job_id_str, "completed", 100.0, "completed")
                return

            for file_path in files_to_process:
                await _process_single_file(file_path, db, options, job_id_str)
                job.assets_processed += 1
                job.progress = min(99.0, (job.assets_processed / job.assets_queued) * 100.0)
                await db.commit()

            job.status = "completed"
            job.progress = 100.0
            await db.commit()
            await publish_job_progress(job_id_str, "completed", 100.0, "completed")

        except Exception as exc:
            logger.exception(f"Critical error in ingest pipeline for job {job_id_str}")
            job.status = "failed"
            job.progress = getattr(job, "progress", 0.0) or 0.0
            job.error_message = str(exc)
            await db.commit()
            await publish_job_progress(
                job_id_str,
                "failed",
                job.progress,
                "failed",
                error_message=str(exc),
            )

from ai_pipeline.models.refinement_llm import create_refinement_llm

async def run_regenerate_insights_job(job_id_str: str, asset_id_str: str) -> None:
    logger.info(f"Starting regenerate insights job {job_id_str} for asset: {asset_id_str}")
    await publish_job_progress(job_id_str, "processing", 10.0, "fetching_data")

    try:
        async with SessionLocal() as db:
            asset_uuid = uuid.UUID(asset_id_str)
            asset = await db.get(Asset, asset_uuid)
            if not asset:
                raise ValueError("Asset not found")

            # Fetch scenes
            scenes_result = await db.execute(select(Scene).where(Scene.asset_id == asset_uuid).order_by(Scene.scene_index))
            scenes = scenes_result.scalars().all()

            if not scenes:
                raise ValueError("No scenes found for asset")

            await publish_job_progress(job_id_str, "processing", 30.0, "aggregating_text")

            # Aggregate text
            aggregated_texts = []
            if asset.full_transcript:
                aggregated_texts.append(f"Full Transcript: {asset.full_transcript}")
            for scene in scenes:
                scene_text = f"Scene {scene.scene_index}: [{scene.timestamp_start_sec}s - {scene.timestamp_end_sec}s] "
                if scene.caption:
                    scene_text += f"Caption: {scene.caption}. "
                if scene.transcript_snippet:
                    scene_text += f"Dialogue: {scene.transcript_snippet}."
                aggregated_texts.append(scene_text)
            
            full_text = "\n".join(aggregated_texts)

            await publish_job_progress(job_id_str, "processing", 50.0, "generating_insights")

            # Run LLM
            loop = asyncio.get_running_loop()
            llm = await loop.run_in_executor(None, create_refinement_llm)
            if not llm:
                raise RuntimeError("Failed to initialize Refinement LLM")

            insights = await loop.run_in_executor(None, llm.generate_asset_insights, full_text)
            
            await publish_job_progress(job_id_str, "processing", 90.0, "saving_results")

            # Update DB
            asset.summary = insights.get("summary")
            asset.moods = insights.get("moods", [])
            asset.objects = insights.get("objects", [])
            asset.best_for = insights.get("best_for", [])

            await db.commit()

            await publish_job_progress(job_id_str, "completed", 100.0, "completed")

    except Exception as e:
        logger.exception(f"Regenerate insights failed for job {job_id_str}")
        await publish_job_progress(job_id_str, "failed", 0.0, "failed", error_message=str(e))

from sqlalchemy import delete
from core.embeddings.factory import get_vector_store

async def run_reingest_pipeline(
    job_id_str: str,
    asset_id_str: str,
    options: IngestOptions,
) -> None:
    logger.info(f"Starting reingest pipeline for asset {asset_id_str} (Job: {job_id_str})")
    await publish_job_progress(job_id_str, "processing", 5.0, "initializing")

    local_video_path = None
    try:
        async with SessionLocal() as db:
            asset_uuid = uuid.UUID(asset_id_str)
            asset = await db.get(Asset, asset_uuid)
            if not asset:
                raise ValueError("Asset not found")

            # Download source file from S3 to local
            if not asset.file_path:
                raise ValueError("Asset has no file_path associated for reingestion")

            from ai_pipeline.config import config as ai_config
            local_video_path = Path(ai_config.OUTPUT_DIR) / "reingest" / job_id_str / os.path.basename(asset.file_path)
            local_video_path.parent.mkdir(parents=True, exist_ok=True)
            
            await publish_job_progress(job_id_str, "processing", 10.0, "downloading_source")
            
            if storage_service.client:
                loop = asyncio.get_running_loop()
                ok = await loop.run_in_executor(
                    None,
                    storage_service.client.download_file,
                    asset.file_path,
                    str(local_video_path)
                )
                if not ok:
                    raise RuntimeError(f"Failed to download source video {asset.file_path}")
            else:
                raise RuntimeError("Storage client not available")

            await publish_job_progress(job_id_str, "processing", 20.0, "running_pipeline")

            def progress_callback(current_step: str, progress: float) -> None:
                # 20.0 -> 90.0
                mapped_progress = 20.0 + (progress * 0.7)
                asyncio.run_coroutine_threadsafe(
                    publish_job_progress(job_id_str, "processing", mapped_progress, current_step, update_db=False),
                    loop,
                )

            def run_pipeline() -> VideoAnalysisContract:
                mode = getattr(options, "processing_mode", "fast") if options else "fast"
                pipeline = VideoAnalysisPipeline(
                    processing_mode=mode,
                    storage_client=storage_service.client,
                    progress_callback=progress_callback,
                )
                return pipeline.analyze_video(
                    video_path=local_video_path,
                    asset_id=str(asset.id),
                    source_storage_key=asset.file_path,
                )

            analysis = await loop.run_in_executor(None, run_pipeline)

            await publish_job_progress(job_id_str, "processing", 92.0, "atomic_swap")

            # ATOMIC SWAP
            # 1. Delete old vectors
            vector_store = get_vector_store()
            if hasattr(vector_store, "delete_by_asset"):
                if __import__("inspect").iscoroutinefunction(vector_store.delete_by_asset):
                    await vector_store.delete_by_asset(asset_id_str)
                else:
                    vector_store.delete_by_asset(asset_id_str)

            # 2. Delete old scenes from DB. Cascade handles this if we just delete scenes
            await db.execute(delete(Scene).where(Scene.asset_id == asset_uuid))

            # 3. Insert new scenes and update asset
            await _persist_analysis(db, asset, analysis)

            await publish_job_progress(job_id_str, "completed", 100.0, "completed")

    except Exception as e:
        logger.exception(f"Reingest failed for job {job_id_str}")
        await publish_job_progress(job_id_str, "failed", 0.0, "failed", error_message=str(e))
    finally:
        # Cleanup downloaded local file
        if local_video_path and local_video_path.exists():
            try:
                local_video_path.unlink()
                # Optionally remove parent dir if empty
            except Exception as e:
                logger.warning(f"Failed to cleanup temp reingest file {local_video_path}: {e}")