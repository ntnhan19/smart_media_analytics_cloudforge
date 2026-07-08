from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import logging
from typing import List

from database import get_db
from models.asset import Asset
from models.scene import Scene
from schemas.asset import AssetResponse, AssetFavoriteUpdate, PaginatedAssetResponse
from schemas.ingest import IngestOptions, IngestResponse
from services.storage_service import storage_service
from services.ingest_service import run_reingest_pipeline, run_regenerate_insights_job
from core.embeddings.factory import get_vector_store

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])
logger = logging.getLogger(__name__)

def _build_asset_response(asset: Asset) -> AssetResponse:
    thumbnail_s3_key = getattr(asset, 'thumbnail_s3_key', None)
    if not thumbnail_s3_key and hasattr(asset, 'scenes') and asset.scenes:
        thumbnail_s3_key = asset.scenes[0].keyframe_s3_key

    return AssetResponse(
        asset_id=str(asset.id),
        file_name=asset.file_name,
        file_size=asset.file_size_bytes,
        duration=asset.duration_sec,
        status=asset.status if hasattr(asset, 'status') else "ready",
        created_at=asset.ingested_at,
        tags=asset.tags if hasattr(asset, 'tags') else None,
        resolution=asset.resolution if hasattr(asset, 'resolution') else None,
        media_type=asset.media_type if hasattr(asset, 'media_type') else None,
        summary=asset.summary if hasattr(asset, 'summary') else None,
        moods=asset.moods if hasattr(asset, 'moods') else None,
        objects=asset.objects if hasattr(asset, 'objects') else None,
        best_for=asset.best_for if hasattr(asset, 'best_for') else None,
        transcripts_json=asset.transcripts_json if hasattr(asset, 'transcripts_json') else None,
        thumbnail_url=storage_service.get_stream_url(thumbnail_s3_key) if thumbnail_s3_key else None,
        is_favorite=asset.is_favorite if hasattr(asset, 'is_favorite') else False,
    )

@router.get("", response_model=PaginatedAssetResponse)
async def list_assets(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import func
    from models.ingest_job import IngestJob
    
    # Get total count
    total_result = await db.execute(select(func.count(Asset.id)))
    total_count = total_result.scalar() or 0
    
    result = await db.execute(
        select(Asset).order_by(Asset.ingested_at.desc()).limit(limit).offset(offset)
    )
    assets = result.scalars().all()
    if assets:
        asset_ids = [a.id for a in assets]
        jobs_result = await db.execute(
            select(IngestJob.asset_id, IngestJob.status)
            .where(IngestJob.asset_id.in_(asset_ids))
        )
        job_statuses = {row[0]: row[1] for row in jobs_result}
        
        for a in assets:
            a.status = job_statuses.get(a.id, "ready")
            
    return {
        "items": [_build_asset_response(a) for a in assets],
        "total": total_count
    }

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
        return _build_asset_response(asset)
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

        from models.ingest_job import IngestJob
        active_job = await db.execute(
            select(IngestJob).where(
                IngestJob.asset_id == asset_uuid,
                IngestJob.status.in_(["queued", "processing", "pending"])
            )
        )
        if active_job.scalars().first():
            raise HTTPException(status_code=400, detail="Cannot delete asset while it is being processed")

        vector_store = get_vector_store()
        if hasattr(vector_store, "delete_by_asset"):
            if __import__("inspect").iscoroutinefunction(vector_store.delete_by_asset):
                await vector_store.delete_by_asset(asset_id)
            else:
                vector_store.delete_by_asset(asset_id)

        video_key = asset.file_path
        scenes_result = await db.execute(select(Scene).where(Scene.asset_id == asset_uuid))
        scenes = scenes_result.scalars().all()
        keyframe_keys = [s.keyframe_s3_key for s in scenes if s.keyframe_s3_key]
        
        await storage_service.delete_asset_files(asset_id, video_key, keyframe_keys)

        await db.delete(asset)
        await db.commit()

        return None
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID format")
    except Exception as e:
        logger.error(f"Error deleting asset: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during deletion")

@router.post("/{asset_id}/reingest", response_model=IngestResponse)
async def reingest_asset(
    asset_id: str,
    options: IngestOptions,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    try:
        asset_uuid = uuid.UUID(asset_id)
        asset = await db.get(Asset, asset_uuid)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        from models.ingest_job import IngestJob
        new_job = IngestJob(status="queued", asset_id=asset_uuid)
        db.add(new_job)
        await db.commit()
        await db.refresh(new_job)
        
        job_id_str = str(new_job.job_id)
        background_tasks.add_task(run_reingest_pipeline, job_id_str, asset_id, options)
        return IngestResponse(
            job_id=job_id_str, 
            asset_id=asset_id, 
            status="queued", 
            assets_queued=1, 
            message="Re-ingestion pipeline started."
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID format")

@router.post("/{asset_id}/regenerate-insights", response_model=IngestResponse)
async def regenerate_insights(
    asset_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    try:
        asset_uuid = uuid.UUID(asset_id)
        asset = await db.get(Asset, asset_uuid)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        from models.ingest_job import IngestJob
        new_job = IngestJob(status="queued", asset_id=asset_uuid)
        db.add(new_job)
        await db.commit()
        await db.refresh(new_job)

        job_id_str = str(new_job.job_id)
        background_tasks.add_task(run_regenerate_insights_job, job_id_str, asset_id)
        return IngestResponse(
            job_id=job_id_str, 
            asset_id=asset_id, 
            status="queued", 
            assets_queued=1, 
            message="Regenerate insights job started."
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID format")

@router.patch("/{asset_id}/favorite", response_model=AssetResponse)
async def toggle_favorite(
    asset_id: str,
    update_data: AssetFavoriteUpdate,
    db: AsyncSession = Depends(get_db)
):
    try:
        asset_uuid = uuid.UUID(asset_id)
        asset = await db.get(Asset, asset_uuid)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        asset.is_favorite = update_data.is_favorite
        await db.commit()
        await db.refresh(asset)
        
        # Need to re-fetch scenes to build the response properly
        await db.refresh(asset, ['scenes'])
        return _build_asset_response(asset)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID format")
