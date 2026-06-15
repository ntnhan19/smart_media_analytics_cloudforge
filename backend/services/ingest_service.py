import logging
import os
import uuid
import asyncio
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import SessionLocal
from models.ingest_job import IngestJob
from models.asset import Asset
from models.scene import Scene
from core.embeddings.vector_store import VectorStore
from core.embeddings.embedder import TextEmbedder
from core.websocket_manager import manager
from schemas.ingest import IngestOptions

logger = logging.getLogger(__name__)

async def _process_single_file(file_path: str, db: AsyncSession, vector_store: VectorStore, embedder: TextEmbedder, options: IngestOptions):
    """
    Process a single media file.
    Includes fault-tolerant try-except blocks.
    """
    filename = os.path.basename(file_path)
    logger.info(f"Processing file: {filename}")
    
    # 1. Create Asset in DB
    asset_id = str(uuid.uuid4())
    new_asset = Asset(
        id=asset_id,
        file_name=filename,
        file_path=file_path,
        media_type="video" if filename.lower().endswith((".mp4", ".mov", ".avi")) else "audio",
        mime_type="video/mp4", # Simplified for MVP
        size_bytes=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
        status="processing"
    )
    db.add(new_asset)
    await db.commit()
    await db.refresh(new_asset)
    
    # 2. Call AI Modules (Mocked or wrapped here for backend logic)
    # Since ai_pipeline is outside backend module scope natively, we mock the results for DB/VectorStore logic.
    # In a full deployment, we'd import `from ai_pipeline.core.video_processor import SceneDetector`
    
    # Simulate processing time
    await asyncio.sleep(1)
    
    # Dummy scenes data (mimicking ai_pipeline outputs)
    scenes_data = []
    if options.scene_detection:
        scenes_data.append({
            "scene_index": 1,
            "timestamp_start_sec": 0.0,
            "timestamp_end_sec": 5.0,
            "caption": "A dummy scene caption.",
            "transcript_snippet": "Hello world from the video." if options.transcription else None,
            "tags": ["dummy", "test"]
        })
        
    for scene_data in scenes_data:
        # Create DB Scene
        new_scene = Scene(
            id=str(uuid.uuid4()),
            asset_id=asset_id,
            scene_index=scene_data["scene_index"],
            timestamp_start_sec=scene_data["timestamp_start_sec"],
            timestamp_end_sec=scene_data["timestamp_end_sec"],
            caption=scene_data["caption"],
            transcript_snippet=scene_data["transcript_snippet"]
            # tags field not present in current Scene model schema, usually stored in vector store or another table.
        )
        db.add(new_scene)
        
        # 3. Embed and store in VectorStore (ChromaDB)
        # We embed the caption + transcript
        text_to_embed = scene_data["caption"]
        if scene_data["transcript_snippet"]:
            text_to_embed += " " + scene_data["transcript_snippet"]
            
        embedding = await embedder.embed(text_to_embed)
        
        vector_store.collection.add(
            embeddings=[embedding],
            metadatas=[{
                "asset_id": asset_id,
                "file_name": filename,
                "media_type": new_asset.media_type,
                "file_path": file_path,
                "scene_index": scene_data["scene_index"],
                "timestamp_start_sec": scene_data["timestamp_start_sec"],
                "timestamp_end_sec": scene_data["timestamp_end_sec"],
                "caption": scene_data["caption"],
                "transcript_snippet": scene_data["transcript_snippet"] or "",
                "tags": ",".join(scene_data["tags"])
            }],
            ids=[new_scene.id]
        )
        
    new_asset.status = "ready"
    await db.commit()

async def run_ingest_pipeline(job_id_str: str, source_path: str, options: IngestOptions):
    """
    Background task to process ingest jobs asynchronously.
    """
    logger.info(f"Starting ingest pipeline for job_id: {job_id_str}")
    
    async with SessionLocal() as db:
        # Fetch job
        job_id_uuid = uuid.UUID(job_id_str)
        result = await db.execute(select(IngestJob).where(IngestJob.job_id == job_id_uuid))
        job = result.scalar_one_or_none()
        
        if not job:
            logger.error(f"Job {job_id_str} not found in database.")
            return

        try:
            # Find files (for MVP, we assume non-recursive list of .mp4, .wav etc)
            files_to_process = []
            if os.path.exists(source_path) and os.path.isdir(source_path):
                for f in os.listdir(source_path):
                    if f.lower().endswith((".mp4", ".mov", ".avi", ".wav", ".mp3")):
                        files_to_process.append(os.path.join(source_path, f))
            elif os.path.exists(source_path) and os.path.isfile(source_path):
                files_to_process.append(source_path)
            
            job.assets_queued = len(files_to_process)
            job.status = "processing"
            await db.commit()
            
            # Setup Embedder and VectorStore
            embedder = TextEmbedder()
            vector_store = VectorStore()
            
            # Process files
            for idx, file_path in enumerate(files_to_process):
                try:
                    await _process_single_file(file_path, db, vector_store, embedder, options)
                    job.assets_processed += 1
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    # Fault-tolerance: continue processing other files
                
                # Broadcast progress via WebSocket
                await db.commit()
                progress = (job.assets_processed / job.assets_queued) * 100 if job.assets_queued > 0 else 100
                await manager.broadcast_progress(job_id_str, {
                    "event": "progress",
                    "job_id": job_id_str,
                    "assets_queued": job.assets_queued,
                    "assets_processed": job.assets_processed,
                    "progress": progress
                })
                
            job.status = "completed"
            await db.commit()
            
            # Broadcast completion
            await manager.broadcast_progress(job_id_str, {
                "event": "completed",
                "job_id": job_id_str,
                "progress": 100.0
            })
            
        except Exception as e:
            logger.exception(f"Critical error in ingest pipeline for job {job_id_str}")
            job.status = "failed"
            job.error_message = str(e)
            await db.commit()
            await manager.broadcast_progress(job_id_str, {
                "event": "failed",
                "job_id": job_id_str,
                "error": str(e)
            })
