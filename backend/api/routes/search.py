from fastapi import APIRouter, HTTPException, Depends
from schemas.search import SearchRequest, SearchResponse, SearchResult, SceneSnippet
from core.embeddings.embedder import TextEmbedder
from core.embeddings.factory import get_vector_store as get_factory_vector_store
import logging
import time
from services.storage_service import storage_service
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models.asset import Asset
from typing import List
from schemas.search import TagFrequency

router = APIRouter(prefix="/api/v1/search", tags=["search"])
logger = logging.getLogger(__name__)

# Dependencies to allow easier testing
def get_embedder() -> TextEmbedder:
    return TextEmbedder()

def get_vector_store():
    return get_factory_vector_store()

from collections import Counter

@router.get("/tags", response_model=List[TagFrequency])
async def get_popular_tags(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Asset.tags).where(Asset.tags != None))
        all_tags = []
        for row in result.scalars():
            if isinstance(row, list):
                for item in row:
                    if isinstance(item, str):
                        all_tags.append(item.lower())
                    elif isinstance(item, dict):
                        # Trích xuất tag name nếu AI lưu dưới dạng object thay vì string
                        tag_name = item.get("name") or item.get("tag") or item.get("label")
                        if tag_name and isinstance(tag_name, str):
                            all_tags.append(tag_name.lower())
        
        counts = Counter(all_tags)
        tags = [{"tag": t, "count": c} for t, c in counts.most_common(20)]
        return tags
    except Exception as e:
        logger.exception(f"Error fetching tags: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("", response_model=SearchResponse)
async def search_media(
    request: SearchRequest,
    embedder: TextEmbedder = Depends(get_embedder),
    vector_store = Depends(get_vector_store),
    db: AsyncSession = Depends(get_db)
):
    start_time = time.time()
    try:
        # If project_id is provided, get allowed asset_ids
        allowed_asset_ids = None
        if request.filters and request.filters.project_id:
            res = await db.execute(select(Asset.id).where(Asset.project_id == request.filters.project_id))
            allowed_asset_ids = {str(a) for a in res.scalars().all()}
            # If project has no assets, return empty early
            if not allowed_asset_ids:
                return SearchResponse(query=request.query, total_results=0, results=[], processing_time_ms=0)
                
        # Generate embedding
        query_embedding = await embedder.embed(request.query)
        
        # Build filters for vector store
        filters = None
        if request.filters:
            dumped = request.filters.model_dump(exclude_unset=True, exclude_none=True)
            filters = {}
            if "asset_id" in dumped:
                filters["asset_id"] = dumped["asset_id"]
            # Chroma and PGVector currently only fully support asset_id in our implementations
            
            if not filters:
                filters = None
            
        # If we need post-filtering, get more results initially
        fetch_k = request.top_k * 3 if allowed_asset_ids else request.top_k

        # Search Vector Store (handle sync vs async and parameter names difference)
        if __import__("inspect").iscoroutinefunction(vector_store.search):
            raw_results = await vector_store.search(
                query_embedding=query_embedding,
                n_results=fetch_k,
                filters=filters
            )
        else:
            raw_results = vector_store.search(
                query_embedding=query_embedding,
                top_k=fetch_k,
                filters=filters
            )
        
        # Map raw results to Data Contract
        results = []
        for res in raw_results:
            # Handle structure differences between Chroma (nested metadata) and PGVector (flat dict)
            if "metadata" in res:
                metadata = res["metadata"]
                score = res.get("score", 0.0)
                doc_id = res.get("id")
            else:
                metadata = res
                score = 1.0  # Default score for pgvector results
                doc_id = res.get("id") or res.get("scene_id")
                
            res_asset_id = metadata.get("asset_id", "")
            if allowed_asset_ids and res_asset_id not in allowed_asset_ids:
                continue

            scene_snippet = SceneSnippet(
                scene_index=int(metadata.get("scene_index", 0)),
                timestamp_start_sec=float(metadata.get("timestamp_start_sec", 0.0)),
                timestamp_end_sec=float(metadata.get("timestamp_end_sec", 0.0)),
                caption=metadata.get("caption", ""),
                transcript_snippet=metadata.get("transcript_snippet")
            )
            
            # Reconstruct tags from flattened representation if needed
            tags = metadata.get("tags", "")
            if isinstance(tags, str):
                tags_list = [t.strip() for t in tags.split(",") if t.strip()]
            elif isinstance(tags, list):
                tags_list = tags
            else:
                tags_list = []
                
            keyframe_key = metadata.get("thumbnail_url") or metadata.get("keyframe_s3_key")
            thumbnail_url = storage_service.get_stream_url(keyframe_key) if keyframe_key else None
            
            result = SearchResult(
                asset_id=metadata.get("asset_id", ""),
                file_name=metadata.get("file_name", ""),
                media_type=metadata.get("media_type", "video"),
                file_path=metadata.get("file_path", ""),
                thumbnail_url=thumbnail_url,
                score=score,
                scene=scene_snippet,
                tags=tags_list
            )
            results.append(result)
            
        # Slice back to top_k after post-filtering
        results = results[:request.top_k]
            
        elapsed_ms = (time.time() - start_time) * 1000
        return SearchResponse(
            query=request.query,
            total_results=len(results),
            results=results,
            processing_time_ms=round(elapsed_ms, 2)
        )
        
    except ValueError as ve:
        logger.error(f"Validation error during search: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception(f"Internal server error during search: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
