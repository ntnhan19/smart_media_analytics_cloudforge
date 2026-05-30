import uuid
from sqlalchemy import Column, String, Float, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.types import UUID

from database import Base

class Scene(Base):
    __tablename__ = "scenes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    scene_index = Column(Integer, nullable=False)
    timestamp_start_sec = Column(Float, nullable=False)
    timestamp_end_sec = Column(Float, nullable=False)
    caption = Column(Text)
    transcript_snippet = Column(Text)
    keyframe_path = Column(String)

    asset = relationship("Asset", back_populates="scenes")

    __table_args__ = (
        UniqueConstraint('asset_id', 'scene_index', name='uix_asset_scene_index'),
    )
