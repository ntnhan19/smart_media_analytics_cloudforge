from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from database import get_db
from models.asset import Asset
from schemas.asset import MediaStreamResponse
from services.storage_service import storage_service

router = APIRouter(prefix="/api/v1/media", tags=["media"])

@router.get("/stream/{asset_id}", response_model=MediaStreamResponse)
async def get_media_stream(
    asset_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        asset_uuid = uuid.UUID(asset_id)
        asset = await db.get(Asset, asset_uuid)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        stream_url = storage_service.get_stream_url(asset.file_path)
        return MediaStreamResponse(stream_url=stream_url)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID format")

# Fallback route for local static serving if needed
@router.get("/serve")
async def serve_local_media(path: str):
    from fastapi.responses import FileResponse
    import os
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="File not found")
