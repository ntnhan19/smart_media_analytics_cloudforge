"""
Vector Database Client — ChromaDB Integration

Provides:
- Vector embedding storage and retrieval
- Similarity search functionality
- Metadata management
- Collection management
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not available. Install it with: pip install chromadb")

# ── Constants ─────────────────────────────────────────────────────────────────

SCENE_COLLECTION_NAME = "video_frames"
VECTOR_DIM = 1024  # BGE-M3 dimension


# ── Data Models ───────────────────────────────────────────────────────────────

@dataclass
class SceneSearchResult:
    """
    Search result for a scene — mirrors SceneSnippet contract.
    score: cosine similarity in [0, 1], higher = more similar.
    """
    asset_id: str
    file_name: str
    media_type: str
    file_path: str
    thumbnail_url: Optional[str]
    score: float
    scene_index: int
    timestamp_start_sec: float
    timestamp_end_sec: float
    caption: str
    transcript_snippet: Optional[str]
    tags: List[str]


# ── Configuration ─────────────────────────────────────────────────────────────

class VectorDBConfig:
    """Vector database configuration"""

    def __init__(self,
                 persist_dir: Optional[str] = None,
                 collection_name: str = SCENE_COLLECTION_NAME,
                 chroma_host: Optional[str] = None,
                 chroma_port: Optional[int] = None):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port

    @staticmethod
    def from_env() -> "VectorDBConfig":
        """Load configuration from environment variables"""
        return VectorDBConfig(
            persist_dir=os.getenv("CHROMA_PERSIST_DIR", "data/chromadb"),
            collection_name=os.getenv("CHROMA_COLLECTION", SCENE_COLLECTION_NAME),
            chroma_host=os.getenv("CHROMA_HOST"),
            chroma_port=int(os.getenv("CHROMA_PORT", 8000)) if os.getenv("CHROMA_PORT") else None,
        )


# ── Client ────────────────────────────────────────────────────────────────────

class VectorDBClient:
    """ChromaDB client for vector embeddings storage and retrieval"""

    def __init__(self, config: Optional[VectorDBConfig] = None):
        if not CHROMADB_AVAILABLE:
            raise RuntimeError("ChromaDB is not installed. Install with: pip install chromadb")

        self.config = config or VectorDBConfig.from_env()
        self._client = None
        self._collection = None
        self._initialize()

    # ── Initialization ────────────────────────────────────────────────────────

    def _initialize(self):
        """Initialize ChromaDB client and collection"""
        try:
            if self.config.persist_dir:
                Path(self.config.persist_dir).mkdir(parents=True, exist_ok=True)

            if self.config.chroma_host and self.config.chroma_port:
                logger.info(f"Connecting to Chroma server at {self.config.chroma_host}:{self.config.chroma_port}")
                self._client = chromadb.HttpClient(
                    host=self.config.chroma_host,
                    port=self.config.chroma_port,
                )
            else:
                logger.info(f"Initializing local ChromaDB at {self.config.persist_dir}")
                self._client = chromadb.PersistentClient(path=self.config.persist_dir)

            self._collection = self._client.get_or_create_collection(
                name=self.config.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"ChromaDB collection '{self.config.collection_name}' initialized")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    # ── Scene-level API (domain-specific) ────────────────────────────────────

    def upsert_scene(
        self,
        asset_id: str,
        file_name: str,
        media_type: str,
        file_path: str,
        scene_index: int,
        timestamp_start_sec: float,
        timestamp_end_sec: float,
        caption: str,
        embedding: List[float],
        transcript_snippet: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        Upsert a scene embedding into the vector database.

        Uses deterministic ID format ``{asset_id}_scene_{scene_index:04d}``
        so repeated calls on the same scene update rather than duplicate.

        Args:
            asset_id:            Unique video identifier.
            file_name:           Original video filename.
            media_type:          MIME type, e.g. "video/mp4".
            file_path:           Absolute/relative path to the video file.
            scene_index:         0-based index of the scene within the video.
            timestamp_start_sec: Scene start time in seconds.
            timestamp_end_sec:   Scene end time in seconds.
            caption:             AI-generated scene caption.
            embedding:           1024-dim float vector from BGE-M3.
            transcript_snippet:  Optional transcript text for this scene.
            thumbnail_url:       Optional URL/path to the scene thumbnail.
            tags:                Optional list of string tags.

        Returns:
            True on success, False on failure.
        """
        try:
            if not self._collection:
                logger.error("Collection not initialized")
                return False

            # Validate embedding dimension
            if len(embedding) != VECTOR_DIM:
                logger.error(f"Expected {VECTOR_DIM}-dim embedding, got {len(embedding)}")
                return False

            # Build searchable document text
            parts = [caption]
            if transcript_snippet:
                parts.append(transcript_snippet)
            document = ". ".join(parts)

            # ChromaDB metadata only supports str/int/float/bool — serialize tags to CSV
            tags_csv = ",".join(tags) if tags else ""

            scene_id = f"{asset_id}_scene_{scene_index:04d}"

            metadata = {
                "asset_id": asset_id,
                "file_name": file_name,
                "media_type": media_type,
                "file_path": file_path,
                "thumbnail_url": thumbnail_url or "",
                "scene_index": scene_index,
                "timestamp_start_sec": timestamp_start_sec,
                "timestamp_end_sec": timestamp_end_sec,
                "caption": caption,
                "transcript_snippet": transcript_snippet or "",
                "tags": tags_csv,
            }

            self._collection.upsert(
                ids=[scene_id],
                embeddings=[embedding],
                documents=[document],
                metadatas=[metadata],
            )

            logger.debug(f"Upserted scene {scene_id}")
            return True

        except Exception as e:
            logger.error(f"upsert_scene failed for {asset_id} scene {scene_index}: {e}")
            return False

    def query_scenes(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        asset_id: Optional[str] = None,
    ) -> List[SceneSearchResult]:
        """
        Find the most semantically similar scenes to a query embedding.

        Args:
            query_embedding: 1024-dim float vector to search with.
            n_results:       Maximum number of results to return.
            asset_id:        Optional — filter results to a single video.

        Returns:
            List of SceneSearchResult sorted by descending similarity score.
        """
        try:
            if not self._collection:
                logger.error("Collection not initialized")
                return []

            if len(query_embedding) != VECTOR_DIM:
                logger.error(f"Expected {VECTOR_DIM}-dim query embedding, got {len(query_embedding)}")
                return []

            where_filter: Optional[Dict[str, Any]] = None
            if asset_id:
                where_filter = {"asset_id": {"$eq": asset_id}}

            raw = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter,
                include=["metadatas", "distances", "documents"],
            )

            results: List[SceneSearchResult] = []

            ids_list      = raw.get("ids", [[]])[0]
            distances_list = raw.get("distances", [[]])[0]
            metadatas_list = raw.get("metadatas", [[]])[0]

            for _id, distance, meta in zip(ids_list, distances_list, metadatas_list):
                # ChromaDB cosine distance ∈ [0, 2]; convert to similarity ∈ [0, 1]
                score = max(0.0, min(1.0, 1.0 - distance))

                # Deserialize tags from CSV back to list
                tags_raw = meta.get("tags", "")
                tags = [t for t in tags_raw.split(",") if t] if tags_raw else []

                results.append(SceneSearchResult(
                    asset_id=meta.get("asset_id", ""),
                    file_name=meta.get("file_name", ""),
                    media_type=meta.get("media_type", ""),
                    file_path=meta.get("file_path", ""),
                    thumbnail_url=meta.get("thumbnail_url") or None,
                    score=score,
                    scene_index=int(meta.get("scene_index", 0)),
                    timestamp_start_sec=float(meta.get("timestamp_start_sec", 0.0)),
                    timestamp_end_sec=float(meta.get("timestamp_end_sec", 0.0)),
                    caption=meta.get("caption", ""),
                    transcript_snippet=meta.get("transcript_snippet") or None,
                    tags=tags,
                ))

            logger.info(f"query_scenes returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"query_scenes failed: {e}")
            return []

    def delete_by_video_id(self, asset_id: str) -> bool:
        """
        Delete all scene vectors belonging to a video (for re-ingestion).

        Args:
            asset_id: The video's unique identifier.

        Returns:
            True on success, False on failure.
        """
        try:
            if not self._collection:
                logger.error("Collection not initialized")
                return False

            self._collection.delete(where={"asset_id": {"$eq": asset_id}})
            logger.info(f"Deleted all scenes for asset_id='{asset_id}'")
            return True

        except Exception as e:
            logger.error(f"delete_by_video_id failed for '{asset_id}': {e}")
            return False

    # ── Generic low-level API ─────────────────────────────────────────────────

    def add_embeddings(
        self,
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ) -> bool:
        """Add embeddings using the raw ChromaDB API (no duplicate protection)."""
        try:
            if not self._collection:
                logger.error("Collection not initialized")
                return False

            # Fix: chained != does not work as expected in Python
            if not (len(embeddings) == len(documents) == len(metadatas) == len(ids)):
                logger.error("Mismatched lengths: embeddings, documents, metadatas, and ids must be same length")
                return False

            self._collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )
            logger.info(f"Added {len(embeddings)} embeddings to ChromaDB collection")
            return True

        except Exception as e:
            logger.error(f"Failed to add embeddings: {e}")
            return False

    def query(
        self,
        query_embeddings: Optional[List[List[float]]] = None,
        query_texts: Optional[List[str]] = None,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Raw query returning ChromaDB result dict."""
        try:
            if not self._collection:
                return {"error": "Collection not initialized"}

            if query_embeddings is None and query_texts is None:
                return {"error": "No query provided"}

            results = self._collection.query(
                query_embeddings=query_embeddings,
                query_texts=query_texts,
                n_results=n_results,
                where=where,
            )
            logger.info(f"Query returned {len(results['ids'][0]) if results['ids'] else 0} results")
            return results

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {"error": str(e)}

    def get(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Fetch records by IDs or metadata filter."""
        try:
            if not self._collection:
                return {"error": "Collection not initialized"}

            if ids is None and where is None:
                return {"error": "No filter provided"}

            results = self._collection.get(ids=ids, where=where)
            logger.info(f"Retrieved {len(results['ids'])} embeddings")
            return results

        except Exception as e:
            logger.error(f"Get failed: {e}")
            return {"error": str(e)}

    def delete(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Delete records by IDs or metadata filter."""
        try:
            if not self._collection:
                return False

            if ids is None and where is None:
                logger.error("Either ids or where filter must be provided")
                return False

            self._collection.delete(ids=ids, where=where)
            count = len(ids) if ids else "filtered"
            logger.info(f"Deleted {count} embeddings from ChromaDB")
            return True

        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False

    def count(self) -> int:
        """Total number of embeddings in the active collection."""
        try:
            if not self._collection:
                return 0
            c = self._collection.count()
            logger.info(f"Collection contains {c} embeddings")
            return c
        except Exception as e:
            logger.error(f"Count failed: {e}")
            return 0

    # ── Collection management ─────────────────────────────────────────────────

    def update_collection(self, collection_name: str) -> bool:
        """Switch the active collection (creates it if missing)."""
        try:
            self._collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"Switched to collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to switch collection: {e}")
            return False

    def delete_collection(self, collection_name: str) -> bool:
        """Permanently delete a collection."""
        try:
            self._client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False

    def list_collections(self) -> List[str]:
        """List all collection names in the database."""
        try:
            collections = self._client.list_collections()
            names = [c.name for c in collections]
            logger.info(f"Found {len(names)} collections")
            return names
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []


# ── Factory ───────────────────────────────────────────────────────────────────

def get_vector_db_client() -> Optional[VectorDBClient]:
    """Factory function to create a VectorDBClient from environment config."""
    try:
        return VectorDBClient(VectorDBConfig.from_env())
    except Exception as e:
        logger.error(f"Failed to create vector database client: {e}")
        return None