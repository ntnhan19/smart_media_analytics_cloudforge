import os

from .base import TextEmbedder, VisionProvider
from .bedrock import BedrockTextEmbedder, BedrockVisionProvider
from .ollama import OllamaTextEmbedder, OllamaVisionProvider


def _provider_name() -> str:
    return os.getenv("AI_PROVIDER", "local").strip().lower()


def create_vision_provider() -> VisionProvider:
    provider = _provider_name()
    if provider == "local":
        return OllamaVisionProvider()
    if provider == "aws":
        return BedrockVisionProvider(
            model_id=os.getenv("AWS_BEDROCK_MODEL_ID"),
            region_name=os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION"),
        )
    raise ValueError(f"Unsupported AI_PROVIDER='{provider}'")


def create_text_embedder() -> TextEmbedder:
    provider = _provider_name()
    if provider == "local":
        return OllamaTextEmbedder()
    if provider == "aws":
        return BedrockTextEmbedder(
            model_id=os.getenv("AWS_BEDROCK_EMBEDDING_MODEL_ID"),
            region_name=os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION"),
            embedding_dim=int(os.getenv("EMBEDDING_DIM", "1024")),
        )
    raise ValueError(f"Unsupported AI_PROVIDER='{provider}'")
