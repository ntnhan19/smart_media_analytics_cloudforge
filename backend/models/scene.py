"""
models/scene.py
Scene Model - Tối ưu cho Semantic Search và Video Editor
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

try:
    from database import Base
    from config import settings
except ImportError:  # Allows importing as backend.models.scene from repo root.
    from backend.database import Base
    from backend.config import settings


class Scene(Base):
    __tablename__ = "scenes"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Relationship với Asset
    asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Scene Information
    scene_index = Column(Integer, nullable=False)
    timestamp_start_sec = Column(Float, nullable=False)
    timestamp_end_sec = Column(Float, nullable=False)

    # Display Content
    caption = Column(Text, nullable=True)                # Mô tả từ Vision + Refinement
    transcript_snippet = Column(Text, nullable=True)     # Đoạn lời thoại tương ứng

    # Semantic Search Fields (RẤT QUAN TRỌNG)
    searchable_text = Column(Text, nullable=True)        # Text tối ưu cho embedding & search
    semantic_metadata = Column(JSONB, nullable=True, default=dict)

    # Storage
    keyframe_path = Column(String, nullable=True)        # Local path (nếu cần)
    keyframe_s3_key = Column(String, nullable=True)      # Đường dẫn trên MinIO/S3

    # Vector Embedding
    embedding = Column(Vector(settings.EMBEDDING_DIM), nullable=True)

    # Additional Metadata
    tags = Column(JSONB, nullable=True, default=list)    # List of tags
    detected_objects = Column(JSONB, nullable=True, default=list)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship
    asset = relationship("Asset", back_populates="scenes")

    # Constraints & Indexes
    __table_args__ = (
        UniqueConstraint('asset_id', 'scene_index', name='uix_asset_scene_index'),
        
        # Performance indexes
        Index('ix_scene_asset_id', 'asset_id'),
        Index('ix_scene_timestamp', 'timestamp_start_sec'),
        Index('ix_scene_searchable_text', 'searchable_text'),  # Giúp full-text search sau này
    )

    def __repr__(self):
        return f"<Scene {self.scene_index} of asset {self.asset_id}>"

    @property
    def duration_sec(self) -> float:
        """Thời lượng của scene."""
        return round(self.timestamp_end_sec - self.timestamp_start_sec, 2)
