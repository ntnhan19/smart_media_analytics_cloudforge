from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from pgvector.sqlalchemy import Vector
import uuid

from config import settings
from database import SessionLocal
from models.scene import Scene

class PGVectorStore:
    """
    Adapter for PGVector in PostgreSQL, implementing the same conceptual interface as VectorStore (ChromaDB).
    Uses the scenes table to store vectors.
    """
    def __init__(self):
        self.dim = settings.EMBEDDING_DIM

    async def add_embeddings(
        self,
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ):
        """
        Since scenes are usually inserted first without embeddings and then embeddings are updated,
        or embeddings can be inserted along with scenes, here we handle updating existing scenes
        with their embeddings based on the scene ID (ids).
        """
        async with SessionLocal() as db:
            for emb, meta, doc_id in zip(embeddings, metadatas, ids):
                # Update the embedding for the corresponding scene
                scene_uuid = uuid.UUID(doc_id)
                scene = await db.get(Scene, scene_uuid)
                if scene:
                    scene.embedding = emb
                    # metadatas are already stored in scene properties or can be updated if needed
            await db.commit()

    async def search(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform a vector similarity search using Cosine Distance (<=>).
        """
        async with SessionLocal() as db:
            # Query the scenes table, order by cosine distance
            # filters can be applied to asset.media_type or scene.asset_id etc.
            
            stmt = select(Scene).order_by(Scene.embedding.cosine_distance(query_embedding)).limit(n_results)
            
            # Simple filter handling (e.g., {"asset_id": "..."})
            if filters:
                if "asset_id" in filters:
                    stmt = stmt.where(Scene.asset_id == filters["asset_id"])
                    
            result = await db.execute(stmt)
            scenes = result.scalars().all()
            
            results = []
            for scene in scenes:
                # Approximate distance isn't easily accessible without returning it explicitly in the query
                # For simplicity, returning just the metadata mimicking Chroma
                results.append({
                    "id": str(scene.id),
                    "asset_id": str(scene.asset_id),
                    "scene_index": scene.scene_index,
                    "timestamp_start_sec": scene.timestamp_start_sec,
                    "timestamp_end_sec": scene.timestamp_end_sec,
                    "caption": scene.caption,
                    "transcript_snippet": scene.transcript_snippet,
                    "keyframe_s3_key": scene.keyframe_s3_key
                })
            return results

    async def delete_by_asset(self, asset_id: str):
        """
        For PGVector, deleting the Asset in SQLAlchemy cascades to Scenes.
        However, if we want to explicitly delete scenes via adapter, we can do it here.
        """
        async with SessionLocal() as db:
            from sqlalchemy import delete
            await db.execute(delete(Scene).where(Scene.asset_id == uuid.UUID(asset_id)))
            await db.commit()

    async def update_embedding(self, scene_id: str, new_embedding: List[float], metadata_updates: Dict[str, Any] = None):
        """
        Updates an existing embedding.
        """
        async with SessionLocal() as db:
            scene_uuid = uuid.UUID(scene_id)
            scene = await db.get(Scene, scene_uuid)
            if scene:
                scene.embedding = new_embedding
                # SQLAlchemy model updates will be handled by the route directly for caption/transcript
                await db.commit()


