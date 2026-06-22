from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Optional


TagCategory = Literal["theme", "location", "content_type"]


@dataclass
class TagContract:
    name: str
    category: TagCategory = "theme"
    source: Literal["auto"] = "auto"

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

    def __post_init__(self) -> None:
        self.name = self.name.upper()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "occurrences": [occ.to_dict() for occ in self.occurrences],
        }


@dataclass
class SceneAnalysisContract:
    """
    Scene JSON contract aligned with backend.models.Scene.

    PostgreSQL fields:
    - scene_index
    - timestamp_start_sec
    - timestamp_end_sec
    - caption
    - transcript_snippet
    - keyframe_path
    - keyframe_s3_key
    - embedding
    """

    scene_index: int
    timestamp_start_sec: float
    timestamp_end_sec: float
    caption: str
    transcript_snippet: str = ""
    keyframe_path: str = ""
    keyframe_s3_key: str = ""
    embedding: Optional[List[float]] = None
    tags: List[TagContract] = field(default_factory=list)
    detected_objects: List[DetectedObjectContract] = field(default_factory=list)

    @property
    def embedding_text(self) -> str:
        parts = [self.caption.strip(), self.transcript_snippet.strip()]
        tag_text = " ".join(tag.name for tag in self.tags)
        if tag_text:
            parts.append(tag_text)
        return "\n".join(part for part in parts if part)

    def to_dict(self, include_embedding: bool = True) -> Dict[str, Any]:
        data = {
            "scene_index": self.scene_index,
            "timestamp_start_sec": self.timestamp_start_sec,
            "timestamp_end_sec": self.timestamp_end_sec,
            "caption": self.caption,
            "transcript_snippet": self.transcript_snippet,
            "keyframe_path": self.keyframe_path,
            "keyframe_s3_key": self.keyframe_s3_key,
            "tags": [tag.to_dict() for tag in self.tags],
            "detected_objects": [obj.to_dict() for obj in self.detected_objects],
        }
        if include_embedding:
            data["embedding"] = self.embedding
        return data


@dataclass
class VideoAnalysisContract:
    asset_id: str
    file_name: str
    file_path: str
    media_type: str
    duration_sec: float
    resolution: str
    file_size_bytes: int
    full_transcript: str
    tags: List[TagContract]
    scenes: List[SceneAnalysisContract]

    def to_dict(self, include_embeddings: bool = True) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "media_type": self.media_type,
            "duration_sec": self.duration_sec,
            "resolution": self.resolution,
            "file_size_bytes": self.file_size_bytes,
            "full_transcript": self.full_transcript,
            "tags": [tag.to_dict() for tag in self.tags],
            "scenes": [
                scene.to_dict(include_embedding=include_embeddings)
                for scene in self.scenes
            ],
        }
