from fastapi import APIRouter, HTTPException, Depends
from schemas.search import SearchRequest, SearchResponse, SearchResult, SceneSnippet
from core.embeddings.embedder import TextEmbedder
from core.embeddings.factory import get_vector_store as get_factory_vector_store
import logging
import time
from services.storage_service import storage_service

router = APIRouter(prefix="/api/v1/search", tags=["search"])
logger = logging.getLogger(__name__)

# Dependencies to allow easier testing
def get_embedder() -> TextEmbedder:
    return TextEmbedder()

def get_vector_store():
    return get_factory_vector_store()

@router.post("", response_model=SearchResponse)
async def search_media(
    request: SearchRequest,
    embedder: TextEmbedder = Depends(get_embedder),
    vector_store = Depends(get_vector_store)
):
    start_time = time.time()
    try:
        # Generate embedding
        query_embedding = await embedder.embed(request.query)
        
        # Build filters
        filters = None
        if request.filters:
            filters = request.filters.model_dump(exclude_unset=True)
            
        # Search Vector Store (handle sync vs async and parameter names difference)
        if __import__("inspect").iscoroutinefunction(vector_store.search):
            raw_results = await vector_store.search(
                query_embedding=query_embedding,
                n_results=request.top_k,
                filters=filters
            )
        else:
            raw_results = vector_store.search(
                query_embedding=query_embedding,
                top_k=request.top_k,
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
