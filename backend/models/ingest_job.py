import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, func
from sqlalchemy.types import UUID

from database import Base

class IngestJob(Base):
    __tablename__ = "ingest_jobs"

    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String, default="pending")
    assets_queued = Column(Integer, default=0)
    assets_processed = Column(Integer, default=0)
    progress = Column(Float, default=0.0)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
