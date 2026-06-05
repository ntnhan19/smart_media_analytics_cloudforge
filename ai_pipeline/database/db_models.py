"""
Database Models (ORM) — Data Contracts for ChromaDB and PostgreSQL

This module defines the data structures for:
- Video metadata and processing results
- Scene and frame analysis data
- Transcription data with word-level timing
- Embeddings and search metadata
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum


# ── Enums ──────────────────────────────────────────────────────────────────

class VideoStatusEnum(str, Enum):
    """Video processing status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FrameAnalysisTypeEnum(str, Enum):
    """Type of frame analysis"""
    LANDSCAPE = "landscape"
    PORTRAIT = "portrait"
    MOTION = "motion"
    TEXT = "text"
    GENERAL = "general"


class ModelTypeEnum(str, Enum):
    """AI model types used"""
    QWEN_VL = "qwen_vl"
    FLORENCE = "florence"
    WHISPERX = "whisperx"
    BGE_M3 = "bge_m3"
    QWEN_LLM = "qwen_llm"


# ── Video Metadata ────────────────────────────────────────────────────────

@dataclass
class VideoMetadata:
    """Video file metadata and processing info"""
    video_id: str
    file_path: str
    file_name: str
    file_size_mb: float
    duration_sec: float
    width: int
    height: int
    fps: float
    total_frames: int
    codec: str
    bitrate_kbps: int
    
    has_audio: bool
    audio_codec: Optional[str] = None
    
    # Processing metadata
    status: VideoStatusEnum = VideoStatusEnum.QUEUED
    processing_mode: str = "balanced"  # fast | balanced | high | ultra
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Processing results summary
    num_scenes: int = 0
    num_frames: int = 0
    num_frames_analyzed: int = 0
    transcript_length: int = 0
    
    # Error tracking
    error_message: Optional[str] = None
    error_timestamp: Optional[datetime] = None
    
    # Custom tags
    tags: List[str] = field(default_factory=list)
    metadata_custom: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, serializing enums and dates"""
        d = asdict(self)
        d['status'] = self.status.value if isinstance(self.status, VideoStatusEnum) else self.status
        d['created_at'] = self.created_at.isoformat()
        d['updated_at'] = self.updated_at.isoformat()
        if d['completed_at']:
            d['completed_at'] = self.completed_at.isoformat()
        if d['error_timestamp']:
            d['error_timestamp'] = self.error_timestamp.isoformat()
        return d


# ── Scene Data ──────────────────────────────────────────────────────────────

@dataclass
class Scene:
    """Scene segment within a video"""
    scene_id: str  # video_id:scene_index
    video_id: str
    scene_index: int
    
    start_time_sec: float
    end_time_sec: float
    duration_sec: float  # end - start
    midpoint_sec: float  # (start + end) / 2
    
    keyframe_count: int = 0
    has_keyframes: bool = False
    
    # Analysis metadata
    analysis_type: Optional[FrameAnalysisTypeEnum] = None
    confidence_score: float = 0.0
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['analysis_type'] = self.analysis_type.value if isinstance(self.analysis_type, FrameAnalysisTypeEnum) else self.analysis_type
        d['created_at'] = self.created_at.isoformat()
        d['updated_at'] = self.updated_at.isoformat()
        return d


# ── Frame/Keyframe Data ────────────────────────────────────────────────────

@dataclass
class Frame:
    """Individual frame analysis result"""
    frame_id: str  # video_id:scene_index:frame_index
    video_id: str
    scene_id: str
    frame_index: int
    
    # Timing
    timestamp_sec: float
    
    # File reference
    keyframe_path: str  # Path to saved JPEG
    
    # Analysis results
    vision_analysis: Dict[str, Any] = field(default_factory=dict)
    # {
    #     "qwen_vl": "...",
    #     "florence": "...",
    # }
    
    refined_analysis: Dict[str, Any] = field(default_factory=dict)
    # {
    #     "summary": "...",
    #     "searchable_text": "...",
    #     "confidence_score": 0.8,
    #     "tags": ["landscape", "mountain", ...],
    #     "detected_objects": [...],
    # }
    
    # Models used
    models_used: List[ModelTypeEnum] = field(default_factory=list)
    
    # Metadata
    inference_time_ms: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Custom metadata
    metadata_custom: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['models_used'] = [m.value if isinstance(m, ModelTypeEnum) else m for m in self.models_used]
        d['created_at'] = self.created_at.isoformat()
        d['updated_at'] = self.updated_at.isoformat()
        return d


# ── Transcription Data ─────────────────────────────────────────────────────

@dataclass
class TranscriptionSegment:
    """Segment of transcription with word-level details"""
    segment_id: str  # video_id:segment_index
    video_id: str
    segment_index: int
    
    start_time_sec: float
    end_time_sec: float
    
    text: str
    language: str = "en"
    language_confidence: float = 0.0
    
    # Quality metrics
    confidence_avg: float = 0.0
    no_speech_prob: float = 0.0
    compression_ratio: float = 0.0
    
    # Word-level data
    words: List[Dict[str, Any]] = field(default_factory=list)
    # [
    #     {"word": "Hello", "start": 0.1, "end": 0.5, "confidence": 0.95},
    #     ...
    # ]
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['created_at'] = self.created_at.isoformat()
        return d


@dataclass
class Transcript:
    """Full video transcript"""
    transcript_id: str  # video_id:transcript
    video_id: str
    
    full_text: str
    language: str
    duration_sec: float
    
    # Segments
    segments: List[TranscriptionSegment] = field(default_factory=list)
    
    # Statistics
    num_words: int = 0
    num_segments: int = 0
    avg_confidence: float = 0.0
    
    # Model info
    whisper_model: str = "base"
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['segments'] = [s.to_dict() for s in self.segments]
        d['created_at'] = self.created_at.isoformat()
        d['updated_at'] = self.updated_at.isoformat()
        return d


# ── Embedding Data ────────────────────────────────────────────────────────

@dataclass
class FrameEmbedding:
    """Vector embedding for frame analysis text"""
    embedding_id: str  # frame_id:embedding_index
    frame_id: str
    video_id: str
    
    # Embedding vector and metadata
    text_input: str  # Original text that was embedded
    embedding_model: str  # e.g., "BAAI/bge-m3"
    embedding_vector: Optional[List[float]] = None  # Stored in ChromaDB, optional here
    vector_dim: int = 1024
    
    # Text preprocessing
    preprocessing_method: str = "default"
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.embedding_vector:
            d['embedding_vector'] = self.embedding_vector
        else:
            d.pop('embedding_vector', None)
        d['created_at'] = self.created_at.isoformat()
        return d


@dataclass
class SearchResult:
    """Search result from semantic similarity"""
    frame_id: str
    video_id: str
    timestamp_sec: float
    
    scene_id: str
    scene_index: int
    
    # Search score
    similarity_score: float  # 0.0-1.0
    rerank_score: Optional[float] = None  # After reranking
    
    # Frame content summary
    summary_text: str = ""
    searchable_text: str = ""
    
    # For display
    thumbnail_path: Optional[str] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)


# ── Processing Statistics ────────────────────────────────────────────────

@dataclass
class ProcessingStats:
    """Aggregated statistics for a video processing job"""
    video_id: str
    
    # Input stats
    input_duration_sec: float
    input_size_mb: float
    
    # Processing stats
    processing_duration_sec: float
    processing_mode: str
    
    # Output stats
    num_scenes: int
    num_frames_extracted: int
    num_frames_analyzed: int
    num_transcript_words: int
    num_embeddings_generated: int
    
    # Model usage
    models_used: List[str]
    total_inference_time_sec: float
    
    # Resource usage
    peak_gpu_memory_mb: float
    peak_ram_mb: float
    
    # Quality metrics
    avg_frame_confidence: float
    avg_transcript_confidence: float
    
    # Timestamps
    started_at: datetime
    completed_at: datetime
    
    # Status
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['started_at'] = self.started_at.isoformat()
        d['completed_at'] = self.completed_at.isoformat()
        return d


# ── Search Query/Metadata ──────────────────────────────────────────────

@dataclass
class SearchQuery:
    """Recorded search query for analytics"""
    query_id: str
    query_text: str
    user_id: Optional[str] = None
    
    # Query preprocessing
    query_embeddings: Optional[List[float]] = None
    
    # Results
    num_results: int = 0
    top_k_requested: int = 20
    
    # Timing
    query_time_ms: float = 0.0
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['created_at'] = self.created_at.isoformat()
        return d


# ── Helper Functions ───────────────────────────────────────────────────────

def create_video_id(file_name: str) -> str:
    """Generate unique video ID from filename and timestamp"""
    import uuid
    from datetime import datetime
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique = str(uuid.uuid4())[:8]
    return f"vid_{timestamp}_{unique}"


def create_scene_id(video_id: str, scene_index: int) -> str:
    """Generate scene ID"""
    return f"{video_id}:scene_{scene_index}"


def create_frame_id(video_id: str, scene_index: int, frame_index: int) -> str:
    """Generate frame ID"""
    return f"{video_id}:scene_{scene_index}:frame_{frame_index}"


def create_embedding_id(frame_id: str, embedding_index: int = 0) -> str:
    """Generate embedding ID"""
    return f"{frame_id}:emb_{embedding_index}"


def create_transcript_id(video_id: str) -> str:
    """Generate transcript ID"""
    return f"{video_id}:transcript"


def create_search_result(
    frame_id: str,
    video_id: str,
    timestamp_sec: float,
    scene_id: str,
    scene_index: int,
    similarity_score: float,
    summary_text: str = "",
    searchable_text: str = "",
) -> SearchResult:
    """Factory function to create SearchResult"""
    return SearchResult(
        frame_id=frame_id,
        video_id=video_id,
        timestamp_sec=timestamp_sec,
        scene_id=scene_id,
        scene_index=scene_index,
        similarity_score=similarity_score,
        summary_text=summary_text,
        searchable_text=searchable_text,
    )
