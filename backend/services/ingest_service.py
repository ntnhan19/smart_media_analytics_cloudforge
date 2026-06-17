import logging
import os
import uuid
import asyncio
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import SessionLocal
from models.ingest_job import IngestJob
from models.asset import Asset
from models.scene import Scene
from core.embeddings.factory import get_vector_store
from core.embeddings.embedder import TextEmbedder
from core.websocket_manager import manager
from schemas.ingest import IngestOptions

logger = logging.getLogger(__name__)

async def save_ingest_results(db: AsyncSession, vector_store, embedder: TextEmbedder, asset_id: str, scenes_data: List[Dict[str, Any]], new_asset: Asset, file_path: str):
    """
    Parse JSON result from AI pipeline and store in Postgres & PGVectorStore
    """
    embeddings_to_add = []
    metadatas_to_add = []
    ids_to_add = []

    for scene_data in scenes_data:
        # Create DB Scene
        new_scene = Scene(
            id=str(uuid.uuid4()),
            asset_id=asset_id,
            scene_index=scene_data["scene_index"],
            timestamp_start_sec=scene_data["timestamp_start_sec"],
            timestamp_end_sec=scene_data["timestamp_end_sec"],
            caption=scene_data.get("caption", ""),
            transcript_snippet=scene_data.get("transcript_snippet", ""),
            keyframe_s3_key=scene_data.get("keyframe_s3_key", "")
        )
        db.add(new_scene)
        
        # Prepare embedding payload
        text_to_embed = new_scene.caption
        if new_scene.transcript_snippet:
            text_to_embed += " " + new_scene.transcript_snippet
            
        embedding = await embedder.embed(text_to_embed)
        
        # We need to assign embedding directly if using pgvector, but let's use the VectorStore adapter method
        embeddings_to_add.append(embedding)
        metadatas_to_add.append({
            "asset_id": asset_id,
            "file_name": new_asset.file_name,
            "media_type": new_asset.media_type,
            "file_path": file_path,
            "scene_index": new_scene.scene_index,
            "timestamp_start_sec": new_scene.timestamp_start_sec,
            "timestamp_end_sec": new_scene.timestamp_end_sec,
            "caption": new_scene.caption,
            "transcript_snippet": new_scene.transcript_snippet,
            "keyframe_s3_key": new_scene.keyframe_s3_key
        })
        ids_to_add.append(str(new_scene.id))
        
    await db.commit() # Commit scenes first so PGVectorStore can update them
    
    # Store in VectorStore
    if hasattr(vector_store, 'collection'):
        # ChromaDB path
        vector_store.collection.add(
            embeddings=embeddings_to_add,
            metadatas=metadatas_to_add,
            ids=ids_to_add
        )
    else:
        # PGVectorStore path
        await vector_store.add_embeddings(
            embeddings=embeddings_to_add,
            metadatas=metadatas_to_add,
            ids=ids_to_add
        )


async def _process_single_file(file_path: str, db: AsyncSession, vector_store, embedder: TextEmbedder, options: IngestOptions, job_id_str: str):
    """
    Process a single media file, simulating S3 upload and AI Worker logic.
    """
    filename = os.path.basename(file_path)
    logger.info(f"Processing file: {filename}")
    
    # Upload to MinIO/S3
    await manager.publish_progress(job_id_str, {
        "event": "message",
        "job_id": job_id_str,
        "current_step": "uploading_to_s3",
    })
    video_s3_key = f"uploads/{job_id_str}/{filename}"
    
    # Upload the actual file if storage client is configured
    from .storage_service import storage_service
    if storage_service.client and os.path.exists(file_path):
        logger.info(f"Uploading file to MinIO: {file_path} -> {video_s3_key}")
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(
            None, 
            storage_service.client.upload_file, 
            file_path, 
            video_s3_key
        )
        if success:
            logger.info(f"Successfully uploaded {filename} to MinIO.")
        else:
            logger.error(f"Failed to upload {filename} to MinIO.")
    else:
        # Fallback simulate
        await asyncio.sleep(0.5)
    
    # 1. Create Asset in DB
    asset_uuid = uuid.uuid4()
    asset_id = str(asset_uuid)
    new_asset = Asset(
        id=asset_uuid,
        file_name=filename,
        file_path=video_s3_key, # Using S3 key
        media_type="video" if filename.lower().endswith((".mp4", ".mov", ".avi", ".mov")) else "audio",
        file_size_bytes=os.path.getsize(file_path) if os.path.exists(file_path) else 0
    )
    db.add(new_asset)
    await db.commit()
    await db.refresh(new_asset)
    
    # Simulate Worker publishing progress
    steps = []
    if options.scene_detection: steps.append("scene_detection")
    if options.transcription: steps.append("audio_transcription")
    if options.vision_caption: steps.append("frame_analysis")
    
    for step in steps:
        await manager.publish_progress(job_id_str, {
            "event": "message",
            "job_id": job_id_str,
            "current_step": step,
        })
        await asyncio.sleep(0.5)
    
    # Dummy scenes data (mimicking ai_pipeline outputs JSON)
    scenes_data = []
    if options.scene_detection:
        scenes_data.append({
            "scene_index": 1,
            "timestamp_start_sec": 0.0,
            "timestamp_end_sec": 5.0,
            "caption": "A dummy scene caption.",
            "transcript_snippet": "Hello world from the video." if options.transcription else None,
            "keyframe_s3_key": f"keyframes/{asset_id}/1.jpg"
        })
        
    # Process the results
    await save_ingest_results(db, vector_store, embedder, asset_id, scenes_data, new_asset, file_path)
        
    new_asset.status = "ready"
    await db.commit()

async def run_ingest_pipeline(job_id_str: str, source_path: str, options: IngestOptions, is_retry: bool = False):
    """
    Background task to process ingest jobs asynchronously.
    """
    logger.info(f"Starting ingest pipeline for job_id: {job_id_str} (Retry: {is_retry})")
    
    async with SessionLocal() as db:
        # Fetch job
        job_id_uuid = uuid.UUID(job_id_str)
        result = await db.execute(select(IngestJob).where(IngestJob.job_id == job_id_uuid))
        job = result.scalar_one_or_none()
        
        if not job:
            logger.error(f"Job {job_id_str} not found in database.")
            return

        try:
            # Find files
            files_to_process = []
            if source_path and os.path.exists(source_path):
                if os.path.isdir(source_path):
                    for f in os.listdir(source_path):
                        if f.lower().endswith((".mp4", ".mov", ".avi", ".wav", ".mp3")):
                            files_to_process.append(os.path.join(source_path, f))
                else:
                    files_to_process.append(source_path)
            
            # If retry and no source path, we'd normally query Assets for this job. 
            # For simplicity, if empty, we simulate 1 file.
            if is_retry and not files_to_process:
                files_to_process = ["dummy_retry_file.mp4"]

            job.assets_queued = len(files_to_process)
            job.status = "processing"
            await db.commit()
            
            # Setup Embedder and VectorStore
            embedder = TextEmbedder()
            vector_store = get_vector_store()
            
            # Process files
            for idx, file_path in enumerate(files_to_process):
                try:
                    await _process_single_file(file_path, db, vector_store, embedder, options, job_id_str)
                    job.assets_processed += 1
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    # Fault-tolerance
                
                # Broadcast progress via Redis PubSub
                await db.commit()
                progress = (job.assets_processed / job.assets_queued) * 100 if job.assets_queued > 0 else 100
                await manager.publish_progress(job_id_str, {
                    "event": "progress",
                    "job_id": job_id_str,
                    "assets_queued": job.assets_queued,
                    "assets_processed": job.assets_processed,
                    "progress": progress
                })
                
            job.status = "completed"
            await db.commit()
            
            # Broadcast completion
            await manager.publish_progress(job_id_str, {
                "event": "completed",
                "job_id": job_id_str,
                "progress": 100.0,
                "status": "completed"
            })
            
        except Exception as e:
            logger.exception(f"Critical error in ingest pipeline for job {job_id_str}")
            job.status = "failed"
            job.error_message = str(e)
            await db.commit()
            await manager.publish_progress(job_id_str, {
                "event": "failed",
                "job_id": job_id_str,
                "error": str(e),
                "status": "failed"
            })
