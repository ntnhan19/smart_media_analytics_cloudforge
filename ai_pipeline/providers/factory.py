import os

from .base import TextEmbedder, VisionProvider
from .gemini import GeminiProvider
from .ollama import OllamaTextEmbedder, OllamaVisionProvider


def _provider_name() -> str:
    return os.getenv("AI_PROVIDER", "gemini").strip().lower()


def create_vision_provider() -> VisionProvider:
    provider = _provider_name()
    if provider == "local" or provider == "ollama":
        return OllamaVisionProvider()
    if provider == "gemini" or provider == "aws":
        return GeminiProvider()
    raise ValueError(f"Unsupported AI_PROVIDER='{provider}'")


def create_text_embedder() -> TextEmbedder:
    provider = _provider_name()
    if provider == "local" or provider == "ollama":
        return OllamaTextEmbedder()
    if provider == "gemini" or provider == "aws":
        return GeminiProvider()
    raise ValueError(f"Unsupported AI_PROVIDER='{provider}'")
