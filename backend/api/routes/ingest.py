from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from schemas.ingest import IngestRequest, IngestResponse, IngestStatusResponse
from models.ingest_job import IngestJob
from database import get_db
from core.websocket_manager import manager
from core.limiter import limiter
from config import settings
from services.ingest_service import run_ingest_pipeline, run_ingest_pipeline_with_cleanup
import uuid
import logging
import json
import os
import shutil
from pydantic import BaseModel

class WebhookRequest(BaseModel):
    job_id: str
    status: str
    asset_id: Optional[str] = None
    error: Optional[str] = None

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
@limiter.limit(settings.UPLOAD_RATE_LIMIT)
async def upload_ingest_job(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    options: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    try:
        import os
        ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
        if ext not in settings.ALLOWED_EXTENSIONS:
            client_ip = request.client.host if request.client else "unknown"
            logger.warning(f"File upload rejected due to invalid extension: {ext}", extra={"client_ip": client_ip, "endpoint": request.url.path})
            raise HTTPException(status_code=400, detail=f"File extension {ext} not allowed.")
            
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
        asset_id = uuid.uuid4()
        from models.asset import Asset
        media_type = "audio" if ext in {".wav", ".mp3"} else "video"
        
        new_asset = Asset(
            id=asset_id,
            file_name=file.filename or "uploaded_file",
            file_path=f"uploads/pending/{asset_id}",
            media_type=media_type
        )
        db.add(new_asset)
        
        new_job = IngestJob(
            status="queued",
            asset_id=asset_id
        )
        db.add(new_job)
        await db.commit()
        await db.refresh(new_job)
        
        job_id_str = str(new_job.job_id)
        asset_id_str = str(asset_id)
        
        # Save file to temp location
        upload_dir = f"/tmp/uploads/{job_id_str}"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            bytes_read = 0
            CHUNK_SIZE = 1024 * 1024 # 1MB chunks
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                bytes_read += len(chunk)
                if bytes_read > settings.MAX_UPLOAD_SIZE_BYTES:
                    buffer.close()
                    os.remove(file_path)
                    client_ip = request.client.host if request.client else "unknown"
                    logger.warning(f"File upload rejected due to exceeding size limit", extra={"client_ip": client_ip, "endpoint": request.url.path})
                    raise HTTPException(status_code=413, detail="Payload Too Large")
                buffer.write(chunk)
            
        # Start background task with cleanup
        background_tasks.add_task(
            run_ingest_pipeline_with_cleanup,
            job_id_str=job_id_str,
            source_path=upload_dir,
            options=ingest_options
        )
        
        return IngestResponse(
            job_id=job_id_str,
            asset_id=asset_id_str,
            status="queued",
            assets_queued=1,
            message="Ingestion pipeline started from uploaded file."
        )
    except HTTPException:
        raise
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

@router.post("/webhook", response_model=IngestResponse, status_code=202)
async def ingest_webhook(
    request: WebhookRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook endpoint cho Step Functions gọi lại sau khi AI Worker (ECS) chạy xong.
    Sẽ tiếp tục chạy Full AI Pipeline trên backend với cùng một job_id.
    """
    try:
        job_uuid = uuid.UUID(request.job_id)
        result = await db.execute(select(IngestJob).where(IngestJob.job_id == job_uuid))
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if request.status == "failed":
            job.status = "failed"
            job.error_message = request.error
            await db.commit()
            
            from core.websocket_manager import manager
            await manager.publish_progress(request.job_id, {
                "event": "failed",
                "job_id": request.job_id,
                "error": request.error or "Unknown Step Functions error",
                "status": "failed"
            })
            return IngestResponse(
                job_id=request.job_id,
                status="failed",
                assets_queued=job.assets_queued,
                message="Pipeline failed in Step Functions."
            )

        if not job.asset_id:
            raise HTTPException(status_code=400, detail="Job has no associated asset_id")
            
        # Start the rest of the pipeline in the background using the original Job ID
        from schemas.ingest import IngestOptions
        from services.ingest_service import run_reingest_pipeline
        
        # Use default options or fetch from DB if needed
        options = IngestOptions(scene_detection=True, transcription=True, vision_caption=True)
        
        background_tasks.add_task(
            run_reingest_pipeline,
            job_id_str=request.job_id,
            asset_id_str=str(job.asset_id),
            options=options
        )
        
        return IngestResponse(
            job_id=request.job_id,
            asset_id=str(job.asset_id),
            status="processing",
            assets_queued=job.assets_queued,
            message="Webhook received. Continuing ingestion pipeline."
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
