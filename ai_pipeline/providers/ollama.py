import base64
import io
import os
from pathlib import Path
from typing import List, Optional

import requests
from PIL import Image

from .base import TextEmbedder, VisionProvider


DEFAULT_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_VISION_MODEL = os.getenv("QWEN_VL_MODEL") or os.getenv("OLLAMA_MODEL", "qwen2.5vl:3b")
DEFAULT_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-m3:latest")
DEFAULT_EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1024"))


def _resize_image(image: Image.Image, max_size: int = 448) -> Image.Image:
    width, height = image.size
    if max(width, height) <= max_size:
        return image
    scale = max_size / max(width, height)
    return image.resize((int(width * scale), int(height * scale)), Image.Resampling.LANCZOS)


def _image_to_base64(image_path: Path) -> str:
    image = Image.open(image_path).convert("RGB")
    image = _resize_image(image)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


class OllamaVisionProvider(VisionProvider):
    """Vision captioning through the local Ollama HTTP API."""

    def __init__(
        self,
        base_url: str = DEFAULT_OLLAMA_BASE_URL,
        model_name: str = DEFAULT_VISION_MODEL,
        timeout_sec: int = 300,
    ):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout_sec = timeout_sec

    def caption_keyframe(self, image_path: Path, prompt: Optional[str] = None) -> str:
        prompt = prompt or (
            "Describe this video keyframe for semantic search. "
            "Mention the scene type, main subjects, visible objects, action, "
            "location cues, lighting, and mood. Keep it concise."
        )
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "images": [_image_to_base64(Path(image_path))],
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 220,
            },
            "keep_alive": -1,
        }
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=self.timeout_sec,
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()


class OllamaTextEmbedder(TextEmbedder):
    """BGE-M3 embeddings through the local Ollama HTTP API."""

    def __init__(
        self,
        base_url: str = DEFAULT_OLLAMA_BASE_URL,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
        embedding_dim: int = DEFAULT_EMBEDDING_DIM,
        timeout_sec: int = 60,
    ):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.embedding_dim = embedding_dim
        self.timeout_sec = timeout_sec

    def embed_text(self, text: str) -> List[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            response = requests.post(
                f"{self.base_url}/api/embed",
                json={"model": self.model_name, "input": texts},
                timeout=5.0, # Reduced timeout for testing fallback
            )
            response.raise_for_status()
            embeddings = response.json().get("embeddings", [])
            if len(embeddings) != len(texts):
                raise ValueError("Ollama returned an incomplete embedding batch")
            for embedding in embeddings:
                if len(embedding) != self.embedding_dim:
                    raise ValueError(
                        f"Expected {self.embedding_dim}-dim embedding, got {len(embedding)}"
                    )
            return embeddings
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Ollama Embedder unreachable ({e}). Using dummy zero vectors.")
            return [[0.0] * self.embedding_dim for _ in texts]
