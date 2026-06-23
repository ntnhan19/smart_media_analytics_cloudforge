# -*- coding: utf-8 -*-
import uuid
from sqlalchemy import Column, String, Float, BigInteger, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base  
class Asset(Base):
    __tablename__ = "assets"

    # ─── Primary Key ──────────────────────────────────────────────────────────
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ─── File Information ─────────────────────────────────────────────────────
    file_name = Column(String, nullable=False, index=True)
    file_path = Column(String, nullable=False, unique=True, index=True)
    media_type = Column(String(50), default="video")  # video, audio, image...

    # ─── Technical Metadata ────────────────────────────────────────────────────
    duration_sec = Column(Float, nullable=True, index=True)
    resolution = Column(String(20), nullable=True)     # Ví dụ: "1920x1080"
    file_size_bytes = Column(BigInteger, nullable=True)

    # ─── Ingestion Metadata ────────────────────────────────────────────────────
    ingested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ─── Content Metadata & Semantic ──────────────────────────────────────────
    title = Column(String(255), nullable=True)          # Cho editor đặt tên sau
    description = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)               # Tóm tắt tổng thể video
    full_transcript = Column(Text, nullable=True)       # Toàn bộ text bóc từ audio

    # Các trường JSONB tối ưu lưu trữ mảng/đối tượng phức tạp trên PostgreSQL
    tags = Column(JSONB, nullable=True, default=list)   # List of TagContract
    moods = Column(JSONB, nullable=True, default=list)  # Cảm xúc phân cảnh
    objects = Column(JSONB, nullable=True, default=list)# Các vật thể xuất hiện chính
    best_for = Column(JSONB, nullable=True, default=list) # Gợi ý mục đích dựng (TikTok, Intro...)

    # ─── Storage Keys (MinIO / S3) ────────────────────────────────────────────
    thumbnail_s3_key = Column(String, nullable=True)    # Thumbnail đại diện của video
    video_s3_key = Column(String, nullable=True)        # Đường dẫn video gốc trên S3

    # ─── Relationship ─────────────────────────────────────────────────────────
    scenes = relationship(
        "Scene",
        back_populates="asset",
        cascade="all, delete-orphan",
        lazy="selectin",                                # Tối ưu hóa nạp n+1 scene lập tức
    )

    # ─── Representation & Properties ──────────────────────────────────────────
    def __repr__(self):
        return f"<Asset {self.file_name} ({self.duration_sec}s)>"

    @property
    def scene_count(self) -> int:
        """Số lượng scene đã phân tích."""
        return len(self.scenes) if self.scenes else 0