from pathlib import Path
from typing import List, Optional

from .base import TextEmbedder, VisionProvider


class BedrockVisionProvider(VisionProvider):
    """
    AWS Bedrock vision provider placeholder.

    Intended production mapping:
    - Claude 3.5 Sonnet / compatible multimodal model for keyframe captioning.
    - Use boto3 Bedrock Runtime invoke_model/converse API.
    """

    def __init__(self, model_id: Optional[str] = None, region_name: Optional[str] = None):
        self.model_id = model_id
        self.region_name = region_name

    def caption_keyframe(self, image_path: Path, prompt: Optional[str] = None) -> str:
        raise NotImplementedError("Bedrock vision provider is a cloud-ready stub")


class BedrockTextEmbedder(TextEmbedder):
    """
    AWS Bedrock text embedding provider placeholder.

    Intended production mapping:
    - Amazon Titan Text Embeddings v2 or selected embedding model.
    - Must return vectors with the configured EMBEDDING_DIM.
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        region_name: Optional[str] = None,
        embedding_dim: int = 1024,
    ):
        self.model_id = model_id
        self.region_name = region_name
        self.embedding_dim = embedding_dim

    def embed_text(self, text: str) -> List[float]:
        raise NotImplementedError("Bedrock text embedder is a cloud-ready stub")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError("Bedrock text embedder is a cloud-ready stub")
