from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional


class VisionProvider(ABC):
    """Interface for keyframe captioning providers."""

    @abstractmethod
    def caption_keyframe(self, image_path: Path, prompt: Optional[str] = None) -> str:
        """Return a searchable caption for a keyframe image."""


class TextEmbedder(ABC):
    """Interface for text embedding providers."""

    embedding_dim: int

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Return one embedding vector for a single text."""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Return embedding vectors for a batch of texts."""
