"""
Vector Database Client — ChromaDB Integration

Provides:
- VectorDBClient for storing and querying embeddings via ChromaDB
- Mock fallback when ChromaDB is unavailable
- get_vector_db_client() factory function used by VideoAnalysisPipeline
"""

import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class VectorDBClient:
    """Client for ChromaDB vector database operations."""

    def __init__(self, host: str = "localhost", port: int = 8000, collection_name: str = "video_frames"):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._connected = False
        self._connect()

    def _connect(self):
        """Establish connection to ChromaDB."""
        try:
            import chromadb
            self._client = chromadb.HttpClient(host=self.host, port=self.port)
            # Verify connectivity
            self._client.heartbeat()
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._connected = True
            logger.info(f"Connected to ChromaDB at {self.host}:{self.port} — collection='{self.collection_name}'")
        except Exception as e:
            self._connected = False
            logger.warning(f"ChromaDB connection failed: {e}. Embeddings will not be persisted.")

    @property
    def is_connected(self) -> bool:
        return self._connected

    def add_embeddings(
        self,
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ) -> bool:
        """
        Add embeddings to the vector store.

        Args:
            embeddings: List of embedding vectors (List[float]).
            documents: Corresponding text documents.
            metadatas: Metadata dicts for each document.
            ids: Unique IDs for each document.

        Returns:
            bool: True if operation succeeded.
        """
        if not self._connected or self._collection is None:
            logger.warning("[VectorDB] Not connected — skipping add_embeddings.")
            return False

        try:
            self._collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )
            logger.info(f"[VectorDB] Stored {len(ids)} embeddings in ChromaDB.")
            return True
        except Exception as e:
            logger.error(f"[VectorDB] add_embeddings failed: {e}")
            return False

    def query(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Query the vector store for similar embeddings.

        Args:
            query_embedding: Query vector.
            n_results: Number of results to return.
            where: Optional metadata filter dict.

        Returns:
            dict: ChromaDB query result (ids, distances, documents, metadatas).
        """
        if not self._connected or self._collection is None:
            logger.warning("[VectorDB] Not connected — returning empty query result.")
            return {"ids": [[]], "distances": [[]], "documents": [[]], "metadatas": [[]]}

        try:
            kwargs: Dict[str, Any] = {
                "query_embeddings": [query_embedding],
                "n_results": n_results,
                "include": ["documents", "distances", "metadatas"],
            }
            if where:
                kwargs["where"] = where

            results = self._collection.query(**kwargs)
            logger.info(f"[VectorDB] Query returned {len(results['ids'][0])} results.")
            return results
        except Exception as e:
            logger.error(f"[VectorDB] query failed: {e}")
            return {"ids": [[]], "distances": [[]], "documents": [[]], "metadatas": [[]]}

    def delete_by_video_id(self, video_id: str) -> bool:
        """
        Delete all embeddings associated with a video_id.

        Args:
            video_id: The video ID whose embeddings should be removed.

        Returns:
            bool: True if deletion succeeded.
        """
        if not self._connected or self._collection is None:
            logger.warning("[VectorDB] Not connected — skipping delete.")
            return False

        try:
            self._collection.delete(where={"video_id": video_id})
            logger.info(f"[VectorDB] Deleted embeddings for video_id={video_id}.")
            return True
        except Exception as e:
            logger.error(f"[VectorDB] delete_by_video_id failed: {e}")
            return False


# ── Factory Function ──────────────────────────────────────────────────────

def get_vector_db_client() -> Optional[VectorDBClient]:
    """
    Factory function that creates a VectorDBClient from environment variables.

    Environment variables:
        CHROMA_HOST       — ChromaDB host (default: localhost)
        CHROMA_PORT       — ChromaDB port (default: 8000)
        CHROMA_COLLECTION — Collection name (default: video_frames)

    Returns:
        VectorDBClient if ChromaDB is reachable, else None.
    """
    host = os.getenv("CHROMA_HOST", "localhost")
    port = int(os.getenv("CHROMA_PORT", 8000))
    collection = os.getenv("CHROMA_COLLECTION", "video_frames")

    client = VectorDBClient(host=host, port=port, collection_name=collection)

    if not client.is_connected:
        logger.warning(
            "VectorDBClient: ChromaDB is not available. "
            "Pipeline will continue without vector storage."
        )
        return None

    return client
