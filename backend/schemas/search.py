from pydantic import BaseModel, Field
from typing import List, Optional

class TagFrequency(BaseModel):
    tag: str
    count: int

class SearchRequestFilters(BaseModel):
    asset_id: Optional[str] = Field(None, description="Filter by a specific asset ID for in-video search.")
    project_id: Optional[str] = Field(None, description="Filter by a specific project ID.")
    media_type: List[str] = Field(default_factory=list, description="Filter by media type. Empty array = no filter.")
    tags: List[str] = Field(default_factory=list, description="Filter by tags. Empty array = no filter.")

class SearchRequest(BaseModel):
    query: str = Field(..., description="Natural language search query.", json_schema_extra={"example": "person walking on a beach at sunset"})
    filters: Optional[SearchRequestFilters] = None
    top_k: int = Field(10, ge=1, le=50, description="Maximum number of results to return.")

class SceneSnippet(BaseModel):
    scene_index: int
    timestamp_start_sec: float
    timestamp_end_sec: float
    caption: str
    transcript_snippet: Optional[str] = None

class SearchResult(BaseModel):
    asset_id: str
    file_name: str
    media_type: str
    file_path: str
    thumbnail_url: Optional[str] = None
    score: float = Field(..., ge=0.0, le=1.0)
    scene: SceneSnippet
    tags: List[str]

class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResult]
    processing_time_ms: float = Field(..., description="Time taken to process the search request in milliseconds.")
