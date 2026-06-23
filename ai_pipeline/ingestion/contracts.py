"""
contracts.py
Data Contracts cho AI Pipeline - Semantic Video Analysis
Tối ưu cho Semantic Search, Editor Workflow và Database Mapping
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Optional


TagCategory = Literal[
    "theme", "location", "content_type", "person", 
    "object", "topic", "action", "mood"
]


@dataclass
class TagContract:
    """Tag theo đúng yêu cầu của Backend (v0.0.2)"""
    name: str
    category: TagCategory = "theme"
    source: Literal["auto", "manual"] = "auto"

    def __post_init__(self):
        self.name = (self.name or "").strip().lower()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ObjectOccurrenceContract:
    timestamp_start_sec: float
    timestamp_end_sec: float
    confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DetectedObjectContract:
    name: str
    occurrences: List[ObjectOccurrenceContract] = field(default_factory=list)

    def __post_init__(self):
        self.name = (self.name or "").strip().upper()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "occurrences": [occ.to_dict() for occ in self.occurrences],
        }


# =============================================================================
# Semantic Metadata (Cấu trúc rõ ràng)
# =============================================================================

@dataclass
class SceneSemanticMetadata:
    """Cấu trúc ngữ nghĩa có type rõ ràng"""
    people: List[str] = field(default_factory=list)
    objects: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    mood: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)   # tên riêng, thương hiệu, sản phẩm...

    def to_dict(self) -> Dict[str, List[str]]:
        return {k: [v for v in vals if v] for k, vals in asdict(self).items() if vals}


# =============================================================================
# Main Contracts
# =============================================================================

@dataclass
class SceneAnalysisContract:
    """
    Contract chính cho một phân cảnh.
    Được thiết kế tối ưu cho:
    - Semantic Search (pgvector)
    - Hiển thị trên Frontend
    - Mapping sang SQLAlchemy Model
    """
    scene_index: int
    timestamp_start_sec: float
    timestamp_end_sec: float

    # Text hiển thị
    caption: str = ""
    transcript_snippet: str = ""

    # Semantic Search Core
    searchable_text: str = ""
    semantic_metadata: SceneSemanticMetadata = field(default_factory=SceneSemanticMetadata)

    # Storage
    keyframe_path: str = ""
    keyframe_s3_key: str = ""

    # Vector
    embedding: Optional[List[float]] = None

    # Metadata
    tags: List[TagContract] = field(default_factory=list)
    detected_objects: List[DetectedObjectContract] = field(default_factory=list)

    def __post_init__(self):
        # Chuẩn hóa dữ liệu
        self.caption = (self.caption or "").strip()
        self.transcript_snippet = (self.transcript_snippet or "").strip()
        self.searchable_text = (self.searchable_text or "").strip()

        if not isinstance(self.semantic_metadata, SceneSemanticMetadata):
            self.semantic_metadata = SceneSemanticMetadata()

        # Fallback searchable_text
        if not self.searchable_text.strip():
            self.searchable_text = self._build_fallback_searchable_text()

    def _build_fallback_searchable_text(self) -> str:
        """Tạo searchable_text dự phòng khi refinement chưa sinh."""
        parts: List[str] = []

        if self.caption:
            parts.append(self.caption)
        if self.transcript_snippet:
            parts.append(f"Lời thoại: {self.transcript_snippet}")

        # Semantic metadata
        meta_dict = self.semantic_metadata.to_dict()
        for key, values in meta_dict.items():
            if values:
                parts.append(f"{key}: {', '.join(values)}")

        # Tags
        tag_names = [tag.name for tag in self.tags if tag.name]
        if tag_names:
            parts.append(f"Từ khóa: {', '.join(tag_names)}")

        return "\n".join(parts).strip() or f"Phân cảnh số {self.scene_index}"

    @property
    def embedding_text(self) -> str:
        """Text chính thức dùng để sinh embedding."""
        return self.searchable_text.strip() or self._build_fallback_searchable_text()

    def to_dict(self, include_embedding: bool = True) -> Dict[str, Any]:
        data = {
            "scene_index": self.scene_index,
            "timestamp_start_sec": self.timestamp_start_sec,
            "timestamp_end_sec": self.timestamp_end_sec,
            "caption": self.caption,
            "transcript_snippet": self.transcript_snippet,
            "searchable_text": self.searchable_text,
            "semantic_metadata": self.semantic_metadata.to_dict(),
            "keyframe_path": self.keyframe_path,
            "keyframe_s3_key": self.keyframe_s3_key,
            "tags": [tag.to_dict() for tag in self.tags],
            "detected_objects": [obj.to_dict() for obj in self.detected_objects],
        }
        if include_embedding and self.embedding is not None:
            data["embedding"] = self.embedding

        return data


@dataclass
class VideoAnalysisContract:
    """Contract cho toàn bộ một video."""
    asset_id: str
    file_name: str
    file_path: str
    media_type: str = "video"
    duration_sec: float = 0.0
    resolution: str = ""
    file_size_bytes: int = 0
    full_transcript: str = ""

    tags: List[TagContract] = field(default_factory=list)
    scenes: List[SceneAnalysisContract] = field(default_factory=list)

    def to_dict(self, include_embeddings: bool = True) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "media_type": self.media_type,
            "duration_sec": round(self.duration_sec, 2),
            "resolution": self.resolution,
            "file_size_bytes": self.file_size_bytes,
            "full_transcript": self.full_transcript,
            "tags": [tag.to_dict() for tag in self.tags],
            "scenes": [
                scene.to_dict(include_embedding=include_embeddings)
                for scene in self.scenes
            ],
        }