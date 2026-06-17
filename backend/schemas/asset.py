from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class AssetResponse(BaseModel):
    asset_id: str
    file_name: str
    file_size: Optional[int] = None
    duration: Optional[float] = None
    status: str
    created_at: datetime
    tags: Optional[list] = None
    resolution: Optional[str] = None
    media_type: Optional[str] = None

    class Config:
        from_attributes = True

class SceneResponse(BaseModel):
    scene_id: str
    asset_id: str
    scene_index: int
    timestamp_start_sec: float
    timestamp_end_sec: float
    caption: Optional[str] = None
    transcript_snippet: Optional[str] = None
    thumbnail_url: Optional[str] = None

    class Config:
        from_attributes = True

class SceneUpdateRequest(BaseModel):
    caption: Optional[str] = None
    transcript: Optional[str] = None

class MediaStreamResponse(BaseModel):
    stream_url: str
