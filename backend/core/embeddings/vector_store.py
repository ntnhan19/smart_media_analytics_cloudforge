import chromadb
from typing import Any, Dict, List, Optional
from config import settings

class VectorStore:
    def __init__(self, collection_name: str = "sma_scenes"):
        self.client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def search(
        self, 
        query_embedding: List[float], 
        top_k: int = 10, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Queries ChromaDB for similar vectors.
        """
        where_clause = self._build_where_clause(filters) if filters else None
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause,
            include=["metadatas", "distances"]
        )
        
        parsed_results = []
        if not results["ids"] or not results["ids"][0]:
            return parsed_results
            
        # Chroma returns lists of lists since we provided one query_embedding
        ids = results["ids"][0]
        distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(ids)
        metadatas = results["metadatas"][0] if "metadatas" in results and results["metadatas"] else [{}] * len(ids)
        
        for i in range(len(ids)):
            # Convert cosine distance to cosine similarity (score)
            # Chroma returns distance. If metric is cosine, distance is usually 1 - similarity.
            # So similarity = 1 - distance
            score = 1.0 - distances[i] if distances[i] is not None else 0.0
            
            parsed_results.append({
                "id": ids[i],
                "score": score,
                "metadata": metadatas[i]
            })
            
        return parsed_results

    def _build_where_clause(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts the provided search filters into a ChromaDB where clause.
        """
        conditions = []
        
        if "media_type" in filters and filters["media_type"]:
            media_types = filters["media_type"]
            if len(media_types) == 1:
                conditions.append({"media_type": media_types[0]})
            else:
                conditions.append({"media_type": {"$in": media_types}})
                
        # Tags filtering might require special handling depending on how they are stored in ChromaDB
        # Assuming tags are stored as a comma-separated string 'tag1,tag2' or we do a simple exact match for now.
        # If Chroma doesn't natively support array intersection in where clauses, we might need a workaround.
        if "tags" in filters and filters["tags"]:
            # Basic exact match or $in for single tags. Chroma where clause doesn't fully support array overlap.
            # For this MVP, we will try to match the tag directly if the metadata contains it.
            tags = filters["tags"]
            for tag in tags:
                conditions.append({f"tag_{tag}": True}) # Assuming tags are flattened into booleans

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    def delete_by_asset(self, asset_id: str):
        """
        Deletes all embeddings associated with an asset.
        """
        self.collection.delete(where={"asset_id": asset_id})

    def update_embedding(self, scene_id: str, new_embedding: List[float], metadata_updates: Dict[str, Any] = None):
        """
        Updates an existing embedding and its metadata.
        """
        # First retrieve existing metadata if we only want to partially update,
        # but Chroma's update method overwrites provided fields.
        # We assume scene_id is the doc ID.
        if metadata_updates:
            self.collection.update(
                ids=[scene_id],
                embeddings=[new_embedding],
                metadatas=[metadata_updates]
            )
        else:
            self.collection.update(
                ids=[scene_id],
                embeddings=[new_embedding]
            )

