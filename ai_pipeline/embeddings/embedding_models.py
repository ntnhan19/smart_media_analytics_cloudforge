"""
Embedding Models — 100% Ollama-based (Tối ưu Performance + RAM)
- Sử dụng Batch Embedding của Ollama (gửi nhiều texts trong 1 request)
- Reranker: Dummy để tiết kiệm tài nguyên
- Retry + Error handling tốt
"""

import gc
import requests
import numpy as np
import time
from typing import List, Dict, Any, Union, Optional

from ai_pipeline.config import config
from utils.logger import logger, log_model_loading, log_exception

# ── Ollama Configuration ─────────────────────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_EMBEDDING_MODEL = "bge-m3:latest"
MAX_RETRIES = 3
RETRY_DELAY = 1.5
DEFAULT_BATCH_SIZE = 32   # Có thể tăng lên 32-64 tùy máy


def _check_ollama_server() -> bool:
    """Kiểm tra Ollama server."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return response.status_code == 200
    except Exception:
        return False


def _get_ollama_embeddings(texts: List[str], model: str) -> Optional[np.ndarray]:
    """Gọi Ollama API với Batch Embedding (tối ưu performance)."""
    if not texts:
        return np.array([], dtype=np.float32)

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/embed",
                json={
                    "model": model,
                    "input": texts          # ← Quan trọng: gửi cả batch cùng lúc
                },
                timeout=45
            )
            response.raise_for_status()
            data = response.json()
            
            embeddings = data.get("embeddings")
            if embeddings and len(embeddings) == len(texts):
                return np.array(embeddings, dtype=np.float32)
            else:
                logger.warning("Ollama returned incomplete embeddings")
                return None

        except requests.exceptions.RequestException as e:
            if attempt == MAX_RETRIES:
                logger.warning(f"Ollama batch embedding failed after {MAX_RETRIES+1} attempts: {e}")
                return None
            time.sleep(RETRY_DELAY * (attempt + 1))
        except Exception as e:
            logger.warning(f"Ollama embedding error: {e}")
            if attempt == MAX_RETRIES:
                return None
            time.sleep(RETRY_DELAY)

    return None


class EmbeddingModel:
    """EmbeddingModel thuần Ollama - hỗ trợ batch hiệu quả."""

    def __init__(self):
        self.model_name = OLLAMA_EMBEDDING_MODEL
        self.embedding_dim: Optional[int] = None
        self.is_ready = False
        self._initialize_model()

    def _initialize_model(self):
        """Khởi tạo và kiểm tra Ollama."""
        try:
            if not _check_ollama_server():
                logger.error(f"❌ Ollama server chưa chạy tại {OLLAMA_BASE_URL}")
                return

            log_model_loading(self.model_name, "loading")

            resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
            available_models = [m["name"] for m in resp.json().get("models", [])]

            if self.model_name not in available_models:
                logger.error(f"❌ Model '{self.model_name}' chưa được pull. Chạy: ollama pull {self.model_name}")
                return

            # Test batch embedding
            test_emb = _get_ollama_embeddings(["Test batch embedding"], self.model_name)
            if test_emb is not None and test_emb.shape[0] > 0:
                self.embedding_dim = test_emb.shape[1]
                self.is_ready = True
                log_model_loading(self.model_name, "loaded")
                logger.info(f"✅ Ollama Embedding READY: {self.model_name} (dim={self.embedding_dim}, batch supported)")
            else:
                logger.error("Không thể test embedding từ Ollama")

        except Exception as e:
            log_exception(e, "EmbeddingModel._initialize_model")

    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = DEFAULT_BATCH_SIZE,
        **kwargs
    ) -> np.ndarray:
        """Encode với batch processing."""
        if isinstance(texts, str):
            texts = [texts]

        if not self.is_ready:
            logger.warning("Ollama chưa sẵn sàng, trả zero vectors")
            dim = self.embedding_dim or 1024
            return np.zeros((len(texts), dim), dtype=np.float32)

        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_emb = _get_ollama_embeddings(batch, self.model_name)
            
            if batch_emb is not None:
                all_embeddings.append(batch_emb)
            else:
                # Fallback cho batch lỗi
                dim = self.embedding_dim or 1024
                all_embeddings.append(np.zeros((len(batch), dim), dtype=np.float32))
                logger.warning(f"Batch embedding failed at index {i}")

        return np.vstack(all_embeddings) if all_embeddings else np.zeros((len(texts), self.embedding_dim or 1024), dtype=np.float32)

    def get_embedding_dimension(self) -> int:
        return self.embedding_dim or 1024


# Các class còn lại giữ nguyên (RerankerModel, EmbeddingManager...)
class RerankerModel:
    def __init__(self, model_name: str = None):
        logger.debug("Dummy Reranker initialized (Ollama-only mode)")

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = None,
    ) -> List[Dict[str, Any]]:
        if not documents:
            return []
        results = [
            {"index": i, "text": doc, "score": 1.0 - i * 0.001}
            for i, doc in enumerate(documents)
        ]
        if top_k is not None:
            results = results[:top_k]
        return results


class EmbeddingManager:
    def __init__(self):
        self.embedding_model: Optional[EmbeddingModel] = None

    def load_embedding_model(self):
        if self.embedding_model is None:
            self.embedding_model = EmbeddingModel()

    def load_all(self):
        self.load_embedding_model()

    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        if self.embedding_model is None:
            self.load_embedding_model()
        return self.embedding_model.encode(texts)

    def rerank(self, query: str, documents: List[str], top_k: int = None) -> List[Dict[str, Any]]:
        return RerankerModel().rerank(query, documents, top_k)

    def unload_all(self):
        self.embedding_model = None
        gc.collect()
        logger.info("Embedding context cleared (Ollama mode)")


def create_embedding_model() -> EmbeddingModel:
    return EmbeddingModel()

def create_reranker_model() -> RerankerModel:
    return RerankerModel()