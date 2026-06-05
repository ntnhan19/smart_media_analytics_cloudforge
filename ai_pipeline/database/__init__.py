"""
Database Package — ORM Models, Connection Management, and Repositories

Provides:
- Database models (VideoMetadata, Scene, Frame, etc.)
- Connection pooling and transaction management
- Repository pattern for data access
- Query builders for safe SQL construction
"""

from .db_models import (
    VideoMetadata,
    Scene,
    Frame,
    TranscriptionSegment,
    Transcript,
    FrameEmbedding,
    SearchResult,
    ProcessingStats,
    SearchQuery,
    VideoStatusEnum,
    FrameAnalysisTypeEnum,
    ModelTypeEnum,
    # Factory functions
    create_video_id,
    create_scene_id,
    create_frame_id,
    create_embedding_id,
    create_transcript_id,
    create_search_result,
)

from .db_client import (
    DatabaseConfig,
    DatabaseConnection,
    DatabaseClient,
    Repository,
    QueryBuilder,
    BatchInsertBuilder,
    TransactionContext,
    # Helpers
    get_db_client,
    generate_id,
    get_timestamp,
)

from .repositories import (
    VideoRepository,
    SceneRepository,
    FrameRepository,
    TranscriptRepository,
    SearchRepository,
    RepositoryFactory,
)

__all__ = [
    # Models
    "VideoMetadata",
    "Scene",
    "Frame",
    "TranscriptionSegment",
    "Transcript",
    "FrameEmbedding",
    "SearchResult",
    "ProcessingStats",
    "SearchQuery",
    # Enums
    "VideoStatusEnum",
    "FrameAnalysisTypeEnum",
    "ModelTypeEnum",
    # Client
    "DatabaseConfig",
    "DatabaseConnection",
    "DatabaseClient",
    "Repository",
    "QueryBuilder",
    "BatchInsertBuilder",
    "TransactionContext",
    # Repositories
    "VideoRepository",
    "SceneRepository",
    "FrameRepository",
    "TranscriptRepository",
    "SearchRepository",
    "RepositoryFactory",
    # Helpers
    "get_db_client",
    "generate_id",
    "get_timestamp",
    "create_video_id",
    "create_scene_id",
    "create_frame_id",
    "create_embedding_id",
    "create_transcript_id",
    "create_search_result",
]
