"""
models/asset.py
Asset Model - Đồng bộ với AI Pipeline + Backend
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
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

try:
    from database import Base
except ImportError:  # Allows importing as backend.models.asset from repo root.
    from backend.database import Base


class Asset(Base):
    __tablename__ = "assets"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # File Information
    file_name = Column(String, nullable=False, index=True)
    file_path = Column(String, nullable=False, unique=True, index=True)
    media_type = Column(String(50), default="video")  # video, audio, image...

    # Technical Metadata
    duration_sec = Column(Float, nullable=True)
    resolution = Column(String(20), nullable=True)  # ví dụ: "1920x1080"
    file_size_bytes = Column(BigInteger, nullable=True)

    # Ingestion Metadata
    ingested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Content Metadata
    full_transcript = Column(Text, nullable=True)
    title = Column(String(255), nullable=True)           # Cho editor đặt tên sau
    description = Column(Text, nullable=True)

    # Tags & Semantic
    tags = Column(JSONB, nullable=True, default=list)    # List of TagContract

    # Storage
    thumbnail_s3_key = Column(String, nullable=True)     # Thumbnail đại diện của video
    video_s3_key = Column(String, nullable=True)         # Đường dẫn video gốc trên MinIO/S3

    # Relationship
    scenes = relationship(
        "Scene",
        back_populates="asset",
        cascade="all, delete-orphan",
        lazy="selectin",          # Tối ưu khi join scene
    )

    # Indexes cho performance
    __table_args__ = (
        Index("ix_assets_file_name", "file_name"),
        Index("ix_assets_ingested_at", "ingested_at"),
        Index("ix_assets_duration", "duration_sec"),
    )

    def __repr__(self):
        return f"<Asset {self.file_name} ({self.duration_sec}s)>"

    @property
    def scene_count(self) -> int:
        """Số lượng scene đã phân tích."""
        return len(self.scenes) if self.scenes else 0
