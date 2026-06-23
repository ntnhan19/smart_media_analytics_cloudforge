from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from schemas.ingest import IngestRequest, IngestResponse, IngestStatusResponse
from models.ingest_job import IngestJob
from database import get_db
from core.websocket_manager import manager
from services.ingest_service import run_ingest_pipeline, run_ingest_pipeline_with_cleanup
import uuid
import logging
import json
import os
import shutil

router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])
logger = logging.getLogger(__name__)

@router.post("", response_model=IngestResponse, status_code=202)
async def start_ingest_job(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Create a new job in DB
        new_job = IngestJob(
            status="queued"
        )
        db.add(new_job)
        await db.commit()
        await db.refresh(new_job)
        
        job_id_str = str(new_job.job_id)
        
        # Start background task
        background_tasks.add_task(
            run_ingest_pipeline,
            job_id_str=job_id_str,
            source_path=request.source_path,
            options=request.options
        )
        
        return IngestResponse(
            job_id=job_id_str,
            status="queued",
            assets_queued=0,
            message="Ingestion pipeline started."
        )
    except Exception as e:
        logger.error(f"Failed to start ingest job: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/upload", response_model=IngestResponse, status_code=202)
async def upload_ingest_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    options: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Parse options
        from schemas.ingest import IngestOptions
        ingest_options = IngestOptions()
        if options and options.strip():
            try:
                options_dict = json.loads(options)
                ingest_options = IngestOptions(**options_dict)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON provided for options: {options}. Using defaults.")
            
        # Create a new job in DB
        new_job = IngestJob(
            status="queued"
        )
        db.add(new_job)
        await db.commit()
        await db.refresh(new_job)
        
        job_id_str = str(new_job.job_id)
        
        # Save file to temp location
        upload_dir = f"/tmp/uploads/{job_id_str}"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Start background task with cleanup
        background_tasks.add_task(
            run_ingest_pipeline_with_cleanup,
            job_id_str=job_id_str,
            source_path=upload_dir,
            options=ingest_options
        )
        
        return IngestResponse(
            job_id=job_id_str,
            asset_id=None,
            status="queued",
            assets_queued=1,
            message="Ingestion pipeline started from uploaded file."
        )
    except Exception as e:
        logger.error(f"Failed to start ingest job from upload: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/retry/{job_id}", response_model=IngestResponse, status_code=202)
async def retry_ingest_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    try:
        job_uuid = uuid.UUID(job_id)
        result = await db.execute(select(IngestJob).where(IngestJob.job_id == job_uuid))
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Reset job state
        job.status = "queued"
        job.assets_processed = 0
        job.error_message = None
        await db.commit()
        
        # Start background task with dummy path and default options for retry logic
        from schemas.ingest import IngestOptions
        # In a real app we'd fetch previous options/paths from a DB or S3
        background_tasks.add_task(
            run_ingest_pipeline,
            job_id_str=job_id,
            source_path="", # Re-uses existing assets if supported, or handled via DB
            options=IngestOptions(scene_detection=True, transcription=True, vision_caption=True),
            is_retry=True
        )
        
        return IngestResponse(
            job_id=job_id,
            status="queued",
            assets_queued=job.assets_queued,
            message="Ingestion pipeline restarted."
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

@router.get("/status/{job_id}", response_model=IngestStatusResponse)
async def get_ingest_status(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        job_uuid = uuid.UUID(job_id)
        result = await db.execute(select(IngestJob).where(IngestJob.job_id == job_uuid))
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
            
        progress = job.progress if job.progress is not None else (
            job.assets_processed / job.assets_queued * 100 if job.assets_queued > 0 else 0.0
        )
        
        return IngestStatusResponse(
            job_id=job_id,
            asset_id=str(job.asset_id) if job.asset_id else None,
            status=job.status,
            assets_queued=job.assets_queued,
            assets_processed=job.assets_processed,
            progress=progress,
            error_message=job.error_message
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

@router.websocket("/ws/{job_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    # Establish Connection and Start Redis Subscription
    await manager.connect(websocket, job_id)
    
    try:
        # Fetch current status for immediate recovery
        job_uuid = uuid.UUID(job_id)
        result = await db.execute(select(IngestJob).where(IngestJob.job_id == job_uuid))
        job = result.scalar_one_or_none()
        
        if job:
            progress = job.progress if job.progress is not None else (
                job.assets_processed / job.assets_queued * 100 if job.assets_queued > 0 else 0.0
            )
            import json
            # Send initial state over this specific websocket
            await websocket.send_text(json.dumps({
                "event": job.status,
                "job_id": job_id,
                "asset_id": str(job.asset_id) if job.asset_id else None,
                "status": job.status,
                "progress": progress,
                "assets_queued": job.assets_queued,
                "assets_processed": job.assets_processed,
                "error_message": job.error_message
            }))

        while True:
            # We just keep the connection alive, client may send ping/pong
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, job_id)
