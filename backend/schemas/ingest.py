from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class IngestOptions(BaseModel):
    scene_detection: bool = True
    transcription: bool = True
    vision_caption: bool = True
    whisper_model: str = "base"

class IngestRequest(BaseModel):
    source_path: str = Field(..., description="Path to the directory containing media files.", json_schema_extra={"example": "/app/data/media"})
    options: Optional[IngestOptions] = Field(default_factory=IngestOptions)

class IngestResponse(BaseModel):
    job_id: str
    asset_id: Optional[str] = None
    status: str
    assets_queued: int
    message: str

class IngestStatusResponse(BaseModel):
    job_id: str
    asset_id: Optional[str] = None
    status: str
    assets_queued: int
    assets_processed: int
    progress: float
    error_message: Optional[str] = None
