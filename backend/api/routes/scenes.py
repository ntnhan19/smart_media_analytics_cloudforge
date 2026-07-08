from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import logging
from typing import List

from database import get_db
from models.scene import Scene
from schemas.asset import SceneResponse, SceneUpdateRequest
from core.embeddings.factory import get_vector_store
from core.embeddings.embedder import TextEmbedder
from services.storage_service import storage_service

router = APIRouter(prefix="/api/v1", tags=["scenes"])
logger = logging.getLogger(__name__)

embedder = TextEmbedder()

@router.get("/assets/{asset_id}/scenes", response_model=List[SceneResponse])
async def list_scenes(
    asset_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        asset_uuid = uuid.UUID(asset_id)
        result = await db.execute(
            select(Scene)
            .where(Scene.asset_id == asset_uuid)
            .order_by(Scene.timestamp_start_sec)
        )
        scenes = result.scalars().all()
        
        response = []
        for scene in scenes:
            response.append(SceneResponse(
                scene_id=str(scene.id),
                asset_id=str(scene.asset_id),
                scene_index=scene.scene_index,
                timestamp_start_sec=scene.timestamp_start_sec,
                timestamp_end_sec=scene.timestamp_end_sec,
                caption=scene.caption,
                transcript_snippet=scene.transcript_snippet,
                thumbnail_url=storage_service.get_stream_url(scene.keyframe_s3_key) if scene.keyframe_s3_key else None,
                tags=scene.tags
            ))
        return response
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID format")

@router.get("/assets/{asset_id}/scenes/search", response_model=List[SceneResponse])
async def search_scenes_in_asset(
    asset_id: str,
    query: str,
    top_k: int = 5,
    db: AsyncSession = Depends(get_db)
):
    try:
        asset_uuid = uuid.UUID(asset_id)
        
        # Tạo embedding cho câu query
        query_embedding = await embedder.embed(query)
        
        # Tìm kiếm trong vector store với filter asset_id
        vector_store = get_vector_store()
        filters = {"asset_id": asset_id}
        
        if __import__("inspect").iscoroutinefunction(vector_store.search):
            raw_results = await vector_store.search(
                query_embedding=query_embedding,
                n_results=top_k,
                filters=filters
            )
        else:
            raw_results = vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                filters=filters
            )
            
        # Lấy danh sách scene_id từ kết quả search
        scene_ids = []
        scores_by_id = {}
        for res in raw_results:
            metadata = res.get("metadata", res)
            scene_id_str = res.get("id") or metadata.get("scene_id")
            if scene_id_str:
                try:
                    scene_uuid_obj = uuid.UUID(scene_id_str)
                    scene_ids.append(scene_uuid_obj)
                    scores_by_id[scene_uuid_obj] = res.get("score", 0.0)
                except ValueError:
                    continue
                    
        if not scene_ids:
            return []
            
        # Truy vấn DB để lấy thông tin chi tiết các Scene
        result = await db.execute(
            select(Scene)
            .where(Scene.id.in_(scene_ids))
        )
        scenes = result.scalars().all()
        
        # Sắp xếp lại scenes theo thứ tự điểm số của Vector DB (thấp đến cao hoặc tuỳ thuật toán)
        # Thông thường vector distance càng nhỏ càng giống nhau
        scenes.sort(key=lambda s: scores_by_id.get(s.id, float('inf')))
        
        response = []
        for scene in scenes:
            response.append(SceneResponse(
                scene_id=str(scene.id),
                asset_id=str(scene.asset_id),
                scene_index=scene.scene_index,
                timestamp_start_sec=scene.timestamp_start_sec,
                timestamp_end_sec=scene.timestamp_end_sec,
                caption=scene.caption,
                transcript_snippet=scene.transcript_snippet,
                thumbnail_url=storage_service.get_stream_url(scene.keyframe_s3_key) if scene.keyframe_s3_key else None,
                tags=scene.tags
            ))
        return response
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID format")
    except Exception as e:
        logger.error(f"Error searching scenes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during search")

@router.patch("/scenes/{scene_id}", response_model=SceneResponse)
async def update_scene(
    scene_id: str,
    request: SceneUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        scene_uuid = uuid.UUID(scene_id)
        scene = await db.get(Scene, scene_uuid)
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")

        # Update text fields if provided
        updated = False
        if request.caption is not None:
            scene.caption = request.caption
            updated = True
        if request.transcript is not None:
            scene.transcript_snippet = request.transcript
            updated = True

        if updated:
            # Re-embed text
            text_to_embed = scene.caption or ""
            if scene.transcript_snippet:
                text_to_embed += " " + scene.transcript_snippet
                
            new_embedding = await embedder.embed(text_to_embed)
            
            # Update Vector DB
            vector_store = get_vector_store()
            if hasattr(vector_store, "update_embedding"):
                if __import__("inspect").iscoroutinefunction(vector_store.update_embedding):
                    await vector_store.update_embedding(scene_id, new_embedding, metadata_updates={"caption": scene.caption, "transcript_snippet": scene.transcript_snippet})
                else:
                    vector_store.update_embedding(scene_id, new_embedding, metadata_updates={"caption": scene.caption, "transcript_snippet": scene.transcript_snippet})
                    
            await db.commit()
            await db.refresh(scene)

        return SceneResponse(
            scene_id=str(scene.id),
            asset_id=str(scene.asset_id),
            scene_index=scene.scene_index,
            timestamp_start_sec=scene.timestamp_start_sec,
            timestamp_end_sec=scene.timestamp_end_sec,
            caption=scene.caption,
            transcript_snippet=scene.transcript_snippet,
            thumbnail_url=storage_service.get_stream_url(scene.keyframe_s3_key) if scene.keyframe_s3_key else None,
            tags=scene.tags
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scene ID format")
    except Exception as e:
        logger.error(f"Error updating scene: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during update")
