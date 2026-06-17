from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import logging
from typing import List

from database import get_db
from models.asset import Asset
from models.scene import Scene
from schemas.asset import AssetResponse
from services.storage_service import storage_service
from core.embeddings.factory import get_vector_store

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])
logger = logging.getLogger(__name__)

@router.get("", response_model=List[AssetResponse])
async def list_assets(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Asset).order_by(Asset.ingested_at.desc()).limit(limit).offset(offset)
    )
    assets = result.scalars().all()
    
    response = []
    for asset in assets:
        response.append(AssetResponse(
            asset_id=str(asset.id),
            file_name=asset.file_name,
            file_size=asset.file_size_bytes,
            duration=asset.duration_sec,
            status=asset.status if hasattr(asset, 'status') else "ready",
            created_at=asset.ingested_at,
            tags=asset.tags if hasattr(asset, 'tags') else None,
            resolution=asset.resolution if hasattr(asset, 'resolution') else None,
            media_type=asset.media_type if hasattr(asset, 'media_type') else None
        ))
    return response

@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        asset_uuid = uuid.UUID(asset_id)
        asset = await db.get(Asset, asset_uuid)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
            
        return AssetResponse(
            asset_id=str(asset.id),
            file_name=asset.file_name,
            file_size=asset.file_size_bytes,
            duration=asset.duration_sec,
            status=asset.status if hasattr(asset, 'status') else "ready",
            created_at=asset.ingested_at,
            tags=asset.tags if hasattr(asset, 'tags') else None,
            resolution=asset.resolution if hasattr(asset, 'resolution') else None,
            media_type=asset.media_type if hasattr(asset, 'media_type') else None
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID format")

@router.delete("/{asset_id}", status_code=204)
async def delete_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        asset_uuid = uuid.UUID(asset_id)
        asset = await db.get(Asset, asset_uuid)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        # 1. Delete from Vector DB
        vector_store = get_vector_store()
        if hasattr(vector_store, "delete_by_asset"):
            if __import__("inspect").iscoroutinefunction(vector_store.delete_by_asset):
                await vector_store.delete_by_asset(asset_id)
            else:
                vector_store.delete_by_asset(asset_id)

        # 2. Collect files to delete from S3
        video_key = asset.file_path
        
        # Load scenes to get keyframes
        scenes_result = await db.execute(select(Scene).where(Scene.asset_id == asset_uuid))
        scenes = scenes_result.scalars().all()
        keyframe_keys = [s.keyframe_s3_key for s in scenes if s.keyframe_s3_key]
        
        # 3. Delete from S3/MinIO
        await storage_service.delete_asset_files(asset_id, video_key, keyframe_keys)

        # 4. Delete from PostgreSQL (cascade will handle scenes)
        await db.delete(asset)
        await db.commit()

        return None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID format")
    except Exception as e:
        logger.error(f"Error deleting asset: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during deletion")
