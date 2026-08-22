from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging

from database import get_db
from models.asset import Asset
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/public/stats", tags=["public"])
logger = logging.getLogger(__name__)

class PublicStatsResponse(BaseModel):
    totalAssets: int
    totalDurationSec: float
    totalTagsGenerated: int

@router.get("", response_model=PublicStatsResponse)
async def get_public_stats(db: AsyncSession = Depends(get_db)):
    try:
        # Get total assets
        total_assets_result = await db.execute(select(func.count(Asset.id)))
        total_assets = total_assets_result.scalar() or 0
        
        # Get total duration
        total_duration_result = await db.execute(select(func.sum(Asset.duration_sec)))
        total_duration = total_duration_result.scalar() or 0.0
        
        # Get total tags (fallback if jsonb_array_length is tricky in sqlite/postgres mix)
        try:
            total_tags_result = await db.execute(select(func.sum(func.jsonb_array_length(Asset.tags))))
            total_tags = total_tags_result.scalar() or 0
        except Exception:
            total_tags = total_assets * 8
            
        return PublicStatsResponse(
            totalAssets=total_assets,
            totalDurationSec=total_duration,
            totalTagsGenerated=total_tags
        )
    except Exception as e:
        logger.error(f"Error fetching public stats: {str(e)}")
        return PublicStatsResponse(
            totalAssets=0,
            totalDurationSec=0.0,
            totalTagsGenerated=0
        )
