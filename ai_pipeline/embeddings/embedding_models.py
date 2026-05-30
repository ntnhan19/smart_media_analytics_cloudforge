"""
Embedding Models — tối ưu GTX 1650 4GB
BGE-M3 và BGE-Reranker chạy trên CPU (không tốn VRAM).
Lý do: embedding model chạy CPU cũng đủ nhanh (< 100ms/query),
và để dành toàn bộ 4GB VRAM cho vision/LLM models.
"""

import gc
import torch
import numpy as np
from typing import List, Dict, Any, Union
from FlagEmbedding import BGEM3FlagModel, FlagReranker

from config import config
from utils.logger import logger, log_model_loading, log_exception


class EmbeddingModel:
    """
    BGE-M3 — chạy CPU.
    use_fp16=False vì CPU không hỗ trợ fp16 tốt.
    batch_size nhỏ hơn để tiết kiệm RAM.
    """

    def __init__(self, model_name: str = None, device: str = None):
        self.model_name = model_name or config.model.embedding_model
        # Force CPU để tiết kiệm VRAM cho vision models
        self.device     = "cpu"
        self.model      = None
        self._load_model()

    def _load_model(self):
        try:
            log_model_loading(self.model_name, "loading")

            self.model = BGEM3FlagModel(
                self.model_name,
                use_fp16=False,   # CPU không hỗ trợ fp16 ổn định
            )

            log_model_loading(self.model_name, "loaded")

        except Exception as e:
            log_model_loading(self.model_name, "failed")
            log_exception(e, "EmbeddingModel._load_model")
            raise

    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 4,     # 12 → 4, tiết kiệm RAM
        max_length:  int = 512,
    ) -> np.ndarray:
        try:
            if isinstance(texts, str):
                texts = [texts]

            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                max_length=max_length,
                return_dense=True,
                return_sparse=False,
                return_colbert_vecs=False,
            )

            if isinstance(embeddings, dict):
                return embeddings["dense_vecs"]
            return embeddings

        except Exception as e:
            log_exception(e, "EmbeddingModel.encode")
            return np.array([])

    def encode_queries(
        self,
        queries: Union[str, List[str]],
        max_length: int = 256,
    ) -> np.ndarray:
        return self.encode(queries, batch_size=1, max_length=max_length)

    def encode_corpus(
        self,
        corpus: List[str],
        batch_size: int = 4,
        max_length: int = 512,
        show_progress: bool = True,
    ) -> np.ndarray:
        try:
            all_embeddings = []
            for i in range(0, len(corpus), batch_size):
                batch = corpus[i : i + batch_size]
                emb   = self.encode(batch, batch_size=len(batch), max_length=max_length)
                all_embeddings.append(emb)
                if show_progress and (i + batch_size) % 50 == 0:
                    logger.info(f"Encoded {min(i+batch_size, len(corpus))}/{len(corpus)}")
                gc.collect()   # giải phóng RAM sau mỗi batch

            return np.vstack(all_embeddings)

        except Exception as e:
            log_exception(e, "EmbeddingModel.encode_corpus")
            return np.array([])

    def get_embedding_dimension(self) -> int:
        return self.encode("test").shape[-1]


class RerankerModel:
    """
    BGE-Reranker-v2-m3 — chạy CPU.
    Reranker nhỏ (~280MB), đủ nhanh trên CPU cho top-5 results.
    """

    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.model.reranker_model
        self.model      = None
        self._load_model()

    def _load_model(self):
        try:
            log_model_loading(self.model_name, "loading")

            self.model = FlagReranker(
                self.model_name,
                use_fp16=False,   # CPU
            )

            log_model_loading(self.model_name, "loaded")

        except Exception as e:
            log_model_loading(self.model_name, "failed")
            log_exception(e, "RerankerModel._load_model")
            raise

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = None,
    ) -> List[Dict[str, Any]]:
        try:
            if not documents:
                return []

            pairs  = [[query, doc] for doc in documents]
            scores = self.model.compute_score(pairs, normalize=True)

            if not isinstance(scores, list):
                scores = [scores]

            results = [
                {"index": i, "text": doc, "score": float(score)}
                for i, (doc, score) in enumerate(zip(documents, scores))
            ]
            results.sort(key=lambda x: x["score"], reverse=True)

            if top_k:
                results = results[:top_k]

            logger.debug(
                f"Reranked {len(documents)} docs, top score: {results[0]['score']:.3f}"
            )
            return results

        except Exception as e:
            log_exception(e, "RerankerModel.rerank")
            return [
                {"index": i, "text": doc, "score": 1.0 - i * 0.01}
                for i, doc in enumerate(documents)
            ]


class EmbeddingManager:
    """Manage embedding + reranking models"""

    def __init__(self):
        self.embedding_model: Optional[EmbeddingModel] = None
        self.reranker_model:  Optional[RerankerModel]  = None

    def load_embedding_model(self):
        if self.embedding_model is None:
            self.embedding_model = EmbeddingModel()

    def load_reranker_model(self):
        if self.reranker_model is None:
            self.reranker_model = RerankerModel()

    def load_all(self):
        self.load_embedding_model()
        if config.search.use_reranker:
            self.load_reranker_model()

    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        if self.embedding_model is None:
            self.load_embedding_model()
        return self.embedding_model.encode(texts)

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = None,
    ) -> List[Dict[str, Any]]:
        if self.reranker_model is None:
            if config.search.use_reranker:
                self.load_reranker_model()
            else:
                return [
                    {"index": i, "text": doc, "score": 1.0}
                    for i, doc in enumerate(documents)
                ]
        return self.reranker_model.rerank(query, documents, top_k)

    def unload_all(self):
        self.embedding_model = None
        self.reranker_model  = None
        gc.collect()


# Thêm Optional import bị thiếu
from typing import Optional

def create_embedding_model() -> EmbeddingModel:
    return EmbeddingModel()

def create_reranker_model() -> RerankerModel:
    return RerankerModel()
