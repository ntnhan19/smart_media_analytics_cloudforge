# -*- coding: utf-8 -*-
"""
ingest_service.py
Background service xử lý ingest job hoàn chỉnh
- Cập nhật trạng thái Job + Asset
- Lưu Scenes + Embedding + Vector Store
- Publish Redis Pub/Sub realtime
- Hỗ trợ retry và error handling tốt
"""

import asyncio
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

# Đảm bảo PATH chính xác khi gọi từ gốc dự án
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# AI Pipeline Contracts & Models
from ai_pipeline.ingestion.contracts import VideoAnalysisContract
from ai_pipeline.ingestion.video_pipeline import VideoAnalysisPipeline
from ai_pipeline.models.refinement_llm import create_refinement_llm
from ai_pipeline.config import config as ai_config

# Core System Components
from core.websocket_manager import manager
from core.embeddings.factory import get_vector_store
from database import SessionLocal

# Database Models
from models.asset import Asset
from models.ingest_job import IngestJob
from models.scene import Scene
from schemas.ingest import IngestOptions
from services.storage_service import storage_service

logger = logging.getLogger(__name__)

SUPPORTED_MEDIA_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv", ".webm", ".wav", ".mp3")


# =============================================================================
# Core Progress Realtime Publisher
# =============================================================================

async def publish_job_progress(
    job_id_str: str,
    status: str,
    progress: float,
    current_step: str,
    error_message: Optional[str] = None,
    update_db: bool = True,  # Flag linh hoạt tránh deadlock đa luồng
    asset_id: Optional[str] = None,
) -> None:
    """Cập nhật trạng thái ingest_jobs và phát tín hiệu realtime qua Redis/Websocket."""
    payload = {
        "job_id": job_id_str,
        "status": status,
        "progress": round(float(progress), 2),
        "current_step": current_step,
        "error_message": error_message,
        "asset_id": asset_id,
    }

    # Chỉ cập nhật DB ở luồng Async chính an toàn
    if update_db:
        try:
            async with SessionLocal() as db:
                job = await db.get(IngestJob, uuid.UUID(job_id_str))
                if job:
                    job.status = status
                    job.progress = float(progress)
                    if error_message:
                        job.error_message = error_message[:500]
                    if asset_id:
                        job.asset_id = uuid.UUID(asset_id)
                    await db.commit()
        except Exception as db_err:
            logger.warning(f"DB progress update skipped to avoid deadlock: {db_err}")

    # Phát tín hiệu thời gian thực cho Editor Frontend
    await manager.publish_progress(job_id_str, payload)


# =============================================================================
# Internal Ingestion Helpers
# =============================================================================

def _media_type_for(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return "audio" if suffix in {".wav", ".mp3"} else "video"


def _discover_files(source_path: str) -> List[str]:
    """Tìm kiếm tất cả các file media hợp lệ trong thư mục cấu hình."""
    if not source_path or not os.path.exists(source_path):
        return []
    
    path = Path(source_path)
    if path.is_file():
        return [str(path)] if path.suffix.lower() in SUPPORTED_MEDIA_EXTENSIONS else []
    
    return [
        str(f) for f in path.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_MEDIA_EXTENSIONS
    ]


async def _create_asset(
    db: AsyncSession,
    file_path: str,
    video_s3_key: str,
) -> Asset:
    """Khởi tạo thực thể Asset sạch trong Database."""
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


async def _persist_analysis(
    db: AsyncSession,
    asset: Asset,
    analysis: VideoAnalysisContract,
) -> None:
    """Lưu và đồng bộ toàn bộ siêu dữ liệu AI sạch vào Database."""
    asset.duration_sec = analysis.duration_sec
    asset.resolution = analysis.resolution
    asset.file_size_bytes = analysis.file_size_bytes
    asset.full_transcript = analysis.full_transcript or ""
    asset.tags = [tag.to_dict() for tag in analysis.tags]

    for scene_data in analysis.scenes:
        scene = Scene(
            id=uuid.uuid4(),
            asset_id=asset.id,
            scene_index=scene_data.scene_index,
            timestamp_start_sec=scene_data.timestamp_start_sec,
            timestamp_end_sec=scene_data.timestamp_end_sec,
            caption=scene_data.caption,
            transcript_snippet=scene_data.transcript_snippet,
            searchable_text=getattr(scene_data, "searchable_text", ""),
            semantic_metadata=scene_data.semantic_metadata.to_dict() if hasattr(scene_data.semantic_metadata, "to_dict") else {},
            keyframe_s3_key=scene_data.keyframe_s3_key,
            embedding=scene_data.embedding,
            tags=[t.to_dict() for t in getattr(scene_data, "tags", [])],
        )
        db.add(scene)

    await db.commit()


async def _process_single_file(
    file_path: str,
    db: AsyncSession,
    options: IngestOptions,
    job_id_str: str,
) -> None:
    """Xử lý phân tích biệt lập cho một file media."""
    filename = os.path.basename(file_path)
    video_s3_key = f"uploads/{job_id_str}/{filename}"

    await publish_job_progress(job_id_str, "processing", 5.0, "uploading_file")

    # Đẩy file media gốc vào MinIO/S3 Storage
    if storage_service.client and os.path.exists(file_path):
        loop = asyncio.get_running_loop()
        success = await loop.run_in_executor(
            None, storage_service.client.upload_file, file_path, video_s3_key
        )
        if not success:
            raise RuntimeError(f"Upload source media failed: {video_s3_key}")

    job = await db.get(IngestJob, uuid.UUID(job_id_str))
    asset = None
    if job and job.asset_id:
        asset = await db.get(Asset, job.asset_id)
        
    if not asset:
        asset = await _create_asset(db, file_path, video_s3_key)
        if job:
            job.asset_id = asset.id
            await db.commit()
    else:
        # Asset đã được tạo sẵn ở router, giờ chỉ cần cập nhật metadata thực
        asset.file_path = video_s3_key
        asset.file_size_bytes = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        await db.commit()

    loop = asyncio.get_running_loop()

    # Callback tối ưu: Đẩy tiến độ dạng threadsafe, ngắt tuyệt đối luồng ghi DB tránh deadlock
    def progress_callback(current_step: str, progress: float) -> None:
        asyncio.run_coroutine_threadsafe(
            publish_job_progress(job_id_str, "processing", progress, current_step, update_db=False, asset_id=str(asset.id)),
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
            video_path=Path(file_path),
            asset_id=str(asset.id),
            source_storage_key=video_s3_key,
        )

    analysis = await loop.run_in_executor(None, run_pipeline)

    await publish_job_progress(job_id_str, "processing", 95.0, "saving_to_database")
    await _persist_analysis(db, asset, analysis)


# =============================================================================
# Public Background Service Tasks (Entry Points)
# =============================================================================

async def run_ingest_pipeline(
    job_id_str: str,
    source_path: str,
    options: IngestOptions,
    is_retry: bool = False,
) -> None:
    """Hàm chạy nền chính cho toàn bộ quá trình nạp dữ liệu (Ingestion Pipeline)."""
    logger.info(f"Starting ingest pipeline for job {job_id_str} | retry={is_retry}")

    async with SessionLocal() as db:
        job = await db.get(IngestJob, uuid.UUID(job_id_str))
        if not job:
            logger.error(f"Job {job_id_str} not found in database.")
            return

        try:
            files = _discover_files(source_path)
            if is_retry and not files:
                raise FileNotFoundError("Retry requires the original source path to be supplied")

            job.assets_queued = len(files)
            job.assets_processed = 0
            job.status = "processing"
            job.progress = 0.0
            job.error_message = None
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
                job.progress = min(99.0, (idx / len(files)) * 100.0)
                await db.commit()

            job.status = "completed"
            job.progress = 100.0
            await db.commit()
            await publish_job_progress(job_id_str, "completed", 100.0, "completed")

        except Exception as exc:
            logger.exception(f"Pipeline failed for job {job_id_str}")
            job.status = "failed"
            job.progress = getattr(job, "progress", 0.0) or 0.0
            job.error_message = str(exc)[:500]
            await db.commit()
            await publish_job_progress(
                job_id_str, "failed", job.progress, "failed", error_message=str(exc)
            )

async def run_ingest_pipeline_with_cleanup(
    job_id_str: str,
    source_path: str,
    options: IngestOptions,
) -> None:
    """Hàm chạy nền nạp dữ liệu từ upload có dọn dẹp file tạm."""
    try:
        await run_ingest_pipeline(job_id_str, source_path, options)
    finally:
        import shutil
        if os.path.exists(source_path):
            try:
                shutil.rmtree(source_path)
                logger.info(f"Cleaned up temp upload directory: {source_path}")
            except Exception as e:
                logger.error(f"Failed to cleanup temp directory {source_path}: {e}")


async def run_regenerate_insights_job(job_id_str: str, asset_id_str: str) -> None:
    """Tái cấu trúc và tạo lại Insight tổng thể cho Asset bằng Refinement LLM."""
    logger.info(f"Starting regenerate insights job {job_id_str} for asset: {asset_id_str}")
    await publish_job_progress(job_id_str, "processing", 10.0, "fetching_data")

    try:
        async with SessionLocal() as db:
            asset_uuid = uuid.UUID(asset_id_str)
            asset = await db.get(Asset, asset_uuid)
            if not asset:
                raise ValueError("Asset not found")

            scenes_result = await db.execute(
                select(Scene).where(Scene.asset_id == asset_uuid).order_by(Scene.scene_index)
            )
            scenes = scenes_result.scalars().all()

            if not scenes:
                raise ValueError("No scenes found for asset")

            await publish_job_progress(job_id_str, "processing", 30.0, "aggregating_text")

            # Hợp nhất văn bản ngữ cảnh từ Tai và Mắt phục vụ LLM
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

            loop = asyncio.get_running_loop()
            llm = await loop.run_in_executor(None, create_refinement_llm)
            if not llm:
                raise RuntimeError("Failed to initialize Refinement LLM")

            try:
                insights = await loop.run_in_executor(None, llm.generate_asset_insights, full_text)
            finally:
                if llm:
                    llm.unload()
            
            await publish_job_progress(job_id_str, "processing", 90.0, "saving_results")

            # Cập nhật Schema Metadata nội dung nâng cao phục vụ Editor Filter
            asset.summary = insights.get("summary")
            asset.moods = insights.get("moods", [])
            asset.objects = insights.get("objects", [])
            asset.best_for = insights.get("best_for", [])

            await db.commit()
            await publish_job_progress(job_id_str, "completed", 100.0, "completed")

    except Exception as e:
        logger.exception(f"Regenerate insights failed for job {job_id_str}")
        await publish_job_progress(job_id_str, "failed", 0.0, "failed", error_message=str(e))


async def run_reingest_pipeline(
    job_id_str: str,
    asset_id_str: str,
    options: IngestOptions,
) -> None:
    """Nạp lại và phân tích lại video từ tệp lưu trữ MinIO/S3 (Atomic Swap)."""
    logger.info(f"Starting reingest pipeline for asset {asset_id_str} (Job: {job_id_str})")
    await publish_job_progress(job_id_str, "processing", 5.0, "initializing")

    local_video_path = None
    try:
        async with SessionLocal() as db:
            asset_uuid = uuid.UUID(asset_id_str)
            asset = await db.get(Asset, asset_uuid)
            if not asset:
                raise ValueError("Asset not found")

            if not asset.file_path:
                raise ValueError("Asset has no file_path associated for reingestion")

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

            # ─── ATOMIC SWAP DATA SWAP ────────────────────────────────────────
            # 1. Giải phóng và xóa bỏ toàn bộ Vector Embedding cũ trong kho Vector
            vector_store = get_vector_store()
            if hasattr(vector_store, "delete_by_asset"):
                if __import__("inspect").iscoroutinefunction(vector_store.delete_by_asset):
                    await vector_store.delete_by_asset(asset_id_str)
                else:
                    vector_store.delete_by_asset(asset_id_str)

            # 2. Xóa các phân cảnh cũ khỏi DB (để cascade nạp đè dữ liệu mới)
            await db.execute(delete(Scene).where(Scene.asset_id == asset_uuid))

            # 3. Ghi đè cấu trúc AI Metadata mới sạch sẽ
            await _persist_analysis(db, asset, analysis)

            await publish_job_progress(job_id_str, "completed", 100.0, "completed")

    except Exception as e:
        logger.exception(f"Reingest failed for job {job_id_str}")
        await publish_job_progress(job_id_str, "failed", 0.0, "failed", error_message=str(e))
    finally:
        # Giải phóng tệp tạm cục bộ sau khi hoàn thành nhiệm vụ
        if local_video_path and local_video_path.exists():
            try:
                local_video_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to cleanup temp reingest file {local_video_path}: {e}")