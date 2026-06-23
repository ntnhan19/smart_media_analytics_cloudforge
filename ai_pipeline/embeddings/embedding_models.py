"""
embedding.py
Semantic Embedding Layer cho Video Semantic Search
Tối ưu cho use-case Editor: Upload video → Tìm lại dễ dàng bằng ngôn ngữ tự nhiên
"""

import gc
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import numpy as np
import requests

from ai_pipeline.config import config
from utils.logger import logger, log_model_loading, log_exception


# =============================================================================
# Configuration
# =============================================================================

@dataclass(frozen=True)
class EmbeddingConfig:
    base_url: str = getattr(config, "OLLAMA_BASE_URL", "http://host.docker.internal:11434")
    model: str = "bge-m3:latest"
    timeout: int = 90
    health_timeout: int = 5
    max_retries: int = 3
    retry_delay: float = 1.5
    batch_size: int = 32
    normalize: bool = True


CFG = EmbeddingConfig()


# =============================================================================
# Text Processing
# =============================================================================

def _clean_text(text: str, max_len: int = 2000) -> str:
    """Làm sạch text trước khi embedding."""
    if not text:
        return ""
    text = str(text).replace("\x00", " ")
    text = " ".join(text.split())
    return text[:max_len]


def _normalize_tag(tag: str) -> str:
    """Chuẩn hóa tag: ca_si_nam → ca si nam"""
    if not tag:
        return ""
    tag = str(tag).strip().replace("_", " ").replace("-", " ")
    return " ".join(tag.split())


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    """Giữ thứ tự gốc, loại bỏ trùng lặp."""
    seen = set()
    result = []
    for item in items:
        item = str(item).strip()
        if item and item.lower() not in seen:
            seen.add(item.lower())
            result.append(item)
    return result


# =============================================================================
# Semantic Document Builder
# =============================================================================

def build_scene_semantic_document(
    summary: str = "",
    searchable_text: str = "",
    tags: Optional[Dict[str, Any]] = None,
    transcript_snippet: str = "",
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Xây dựng document tối ưu cho embedding & semantic search.
    Ưu tiên thứ tự: searchable_text > summary > tags > transcript.
    """
    tags = tags or {}
    extra_metadata = extra_metadata or {}

    parts: List[str] = []

    if summary:
        parts.append(f"Tóm tắt: {_clean_text(summary, 600)}")

    if searchable_text:
        parts.append(f"Nội dung chính: {_clean_text(searchable_text, 1100)}")

    # Tags
    scene_tags = _dedupe_preserve_order(
        [_normalize_tag(t) for t in tags.get("scene_tags", [])]
    )
    if scene_tags:
        parts.append(f"Thẻ: {', '.join(scene_tags)}")

    if transcript_snippet:
        parts.append(f"Lời thoại: {_clean_text(transcript_snippet, 800)}")

    # Extra metadata (nếu có)
    if extra_metadata.get("video_domain"):
        parts.append(f"Ngữ cảnh: {extra_metadata['video_domain']}")

    return "\n".join(parts) if parts else "Phân cảnh video"


def build_query_document(query: str) -> str:
    """Chuẩn hóa query từ người dùng/editor."""
    query = _clean_text(query, 1200)
    return f"Truy vấn tìm kiếm: {query}" if query else "tìm video"


# =============================================================================
# Ollama Embedding Client
# =============================================================================

def _is_ollama_healthy(base_url: str) -> bool:
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=CFG.health_timeout)
        return resp.status_code == 200
    except Exception:
        return False


def _get_ollama_embeddings(
    texts: List[str], model: str, base_url: str
) -> Optional[np.ndarray]:
    """Gọi API embedding của Ollama."""
    if not texts:
        return np.zeros((0, 1024), dtype=np.float32)

    try:
        resp = requests.post(
            f"{base_url}/api/embed",
            json={"model": model, "input": texts},
            timeout=CFG.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        embeddings = data.get("embeddings")
        if not embeddings:
            return None

        arr = np.array(embeddings, dtype=np.float32)

        if CFG.normalize:
            norms = np.linalg.norm(arr, axis=1, keepdims=True)
            arr = arr / np.maximum(norms, 1e-12)

        return arr

    except Exception as e:
        logger.warning(f"Ollama embedding error: {e}")
        return None


def _get_embeddings_with_retry(
    texts: List[str], model: str, base_url: str
) -> np.ndarray:
    """Thực hiện retry khi gọi embedding."""
    for attempt in range(CFG.max_retries + 1):
        try:
            result = _get_ollama_embeddings(texts, model, base_url)
            if result is not None:
                return result
        except Exception as e:
            if attempt == CFG.max_retries:
                logger.error(f"Embedding failed after {CFG.max_retries} retries: {e}")
                break

        time.sleep(CFG.retry_delay * (attempt + 1))

    # Fallback: vector zero
    return np.zeros((len(texts), 1024), dtype=np.float32)


# =============================================================================
# Embedding Model
# =============================================================================

class EmbeddingModel:
    """Main class xử lý embedding sử dụng bge-m3."""

    def __init__(self, model_name: Optional[str] = None, base_url: Optional[str] = None):
        self.model_name = model_name or CFG.model
        self.base_url = base_url or CFG.base_url
        self.embedding_dim: int = 1024
        self.is_ready: bool = False

        self._initialize()

    def _initialize(self) -> None:
        try:
            if not _is_ollama_healthy(self.base_url):
                logger.error(f"Ollama server not reachable at {self.base_url}")
                return

            log_model_loading(self.model_name, "loading")

            # Test để lấy dimension thật
            test_emb = _get_embeddings_with_retry(
                ["Test initialization"], self.model_name, self.base_url
            )
            if test_emb.shape[0] > 0:
                self.embedding_dim = test_emb.shape[1]

            self.is_ready = True
            logger.info(
                f"✅ EmbeddingModel ready: {self.model_name} "
                f"(dim={self.embedding_dim}) @ {self.base_url}"
            )

        except Exception as e:
            log_exception(e, "EmbeddingModel._initialize")
            self.is_ready = False

    def encode(self, texts: Union[str, List[str]], batch_size: Optional[int] = None) -> np.ndarray:
        """Encode một hoặc nhiều text."""
        if isinstance(texts, str):
            texts = [texts]

        texts = [_clean_text(t) for t in texts]
        batch_size = batch_size or CFG.batch_size

        if not texts or not self.is_ready:
            return np.zeros((len(texts), self.embedding_dim), dtype=np.float32)

        all_embeddings: List[np.ndarray] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            emb = _get_embeddings_with_retry(batch, self.model_name, self.base_url)
            all_embeddings.append(emb)

        return np.vstack(all_embeddings)

    def encode_query(self, query: str) -> np.ndarray:
        """Embed truy vấn từ editor."""
        doc = build_query_document(query)
        return self.encode(doc)[0]

    def encode_scene_document(
        self,
        summary: str = "",
        searchable_text: str = "",
        tags: Optional[Dict] = None,
        transcript_snippet: str = "",
        extra_metadata: Optional[Dict] = None,
    ) -> np.ndarray:
        """Embed một scene document."""
        doc = build_scene_semantic_document(
            summary=summary,
            searchable_text=searchable_text,
            tags=tags,
            transcript_snippet=transcript_snippet,
            extra_metadata=extra_metadata,
        )
        return self.encode(doc)[0]

    def unload(self) -> None:
        logger.info(f"EmbeddingModel ({self.model_name}) unloaded")
        gc.collect()


# =============================================================================
# Manager & Factory
# =============================================================================

class EmbeddingManager:
    """Facade quản lý embedding."""

    def __init__(self):
        self._model: Optional[EmbeddingModel] = None

    def get_model(self) -> EmbeddingModel:
        if self._model is None:
            self._model = EmbeddingModel()
        return self._model

    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        return self.get_model().encode(texts)

    def encode_query(self, query: str) -> np.ndarray:
        return self.get_model().encode_query(query)

    def encode_scene_document(self, **kwargs) -> np.ndarray:
        return self.get_model().encode_scene_document(**kwargs)

    def unload(self) -> None:
        if self._model:
            self._model.unload()
        self._model = None
        gc.collect()


# =============================================================================
# Factory
# =============================================================================

def create_embedding_model() -> EmbeddingModel:
    return EmbeddingModel()


def create_embedding_manager() -> EmbeddingManager:
    return EmbeddingManager()