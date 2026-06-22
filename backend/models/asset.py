import uuid
from sqlalchemy import Column, String, Float, BigInteger, DateTime, Text, JSON, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
from sqlalchemy.types import UUID

from database import Base

class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False, unique=True)
    media_type = Column(String)
    duration_sec = Column(Float)
    resolution = Column(String)
    file_size_bytes = Column(BigInteger)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())
    full_transcript = Column(Text)
    tags = Column(JSON().with_variant(postgresql.JSONB, 'postgresql'))
    summary = Column(Text)
    moods = Column(JSON().with_variant(postgresql.JSONB, 'postgresql'))
    objects = Column(JSON().with_variant(postgresql.JSONB, 'postgresql'))
    best_for = Column(JSON().with_variant(postgresql.JSONB, 'postgresql'))

    scenes = relationship("Scene", back_populates="asset", cascade="all, delete-orphan")
