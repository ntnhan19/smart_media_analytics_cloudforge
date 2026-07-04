import asyncio
import logging
import os
import tempfile
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.asset import Asset
from services.storage_service import storage_service

router = APIRouter(prefix="/api/v1", tags=["clips"])
logger = logging.getLogger(__name__)

class ClipRequest(BaseModel):
    start_sec: float
    end_sec: float

class ClipResponse(BaseModel):
    clip_url: str

@router.post("/assets/{asset_id}/clip", response_model=ClipResponse)
async def create_video_clip(
    asset_id: str,
    request: ClipRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a sub-clip from an asset's video using FFmpeg and uploads it to storage.
    Returns a download URL.
    """
    try:
        asset_uuid = uuid.UUID(asset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID format")

    asset = await db.get(Asset, asset_uuid)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if not asset.file_path:
        raise HTTPException(status_code=400, detail="Asset source file not found")

    if request.start_sec >= request.end_sec or request.start_sec < 0:
        raise HTTPException(status_code=400, detail="Invalid start/end timestamps")

    # Ensure storage client is available
    if not storage_service.client:
        raise HTTPException(status_code=500, detail="Storage service not configured")

    # Generate internal presigned URL to stream input to ffmpeg from within docker network
    input_url = None
    try:
        from datetime import timedelta
        # Access internal minio client to get the internal URL (minio:9000)
        input_url = storage_service.client._client.presigned_get_object(
            storage_service.client._bucket, 
            asset.file_path, 
            expires=timedelta(seconds=3600)
        )
    except Exception as e:
        logger.error(f"Failed to generate internal presigned URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate input stream URL")

    # Calculate duration
    duration = request.end_sec - request.start_sec
    
    # Destination remote path
    clip_key = f"clips/{asset_id}/{request.start_sec:.2f}_{request.end_sec:.2f}.mp4"

    # Check if we already generated this clip
    if storage_service.client.file_exists(clip_key):
        download_url = storage_service.client.get_presigned_url(clip_key, expires_seconds=3600)
        return ClipResponse(clip_url=download_url)

    # Process ffmpeg in a temporary file
    temp_fd, temp_path = tempfile.mkstemp(suffix=".mp4")
    os.close(temp_fd)

    try:
        # Run ffmpeg to cut the clip. -c copy is fast but may be slightly inaccurate (keyframes).
        # We use -ss before -i for fast seeking.
        cmd = [
            "ffmpeg",
            "-y", # Overwrite
            "-ss", str(request.start_sec),
            "-i", input_url,
            "-t", str(duration),
            "-c", "copy",
            temp_path
        ]
        
        logger.info(f"Running clip generation for asset {asset_id}: {' '.join(cmd)}")
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            logger.error(f"FFmpeg clipping failed. Stderr: {stderr.decode()}")
            raise HTTPException(status_code=500, detail="Failed to generate clip during video processing")

        # Upload the clipped file to MinIO
        loop = asyncio.get_running_loop()
        upload_success = await loop.run_in_executor(
            None,
            storage_service.client.upload_file,
            temp_path,
            clip_key
        )

        if not upload_success:
            raise HTTPException(status_code=500, detail="Failed to upload clip to storage")

        # Generate download URL for the new clip
        download_url = storage_service.client.get_presigned_url(clip_key, expires_seconds=3600)
        
        return ClipResponse(clip_url=download_url)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating clip: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while creating clip")
    finally:
        # Cleanup temp file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"Failed to remove temporary clip file {temp_path}: {e}")
