import httpx
from config import settings

class TextEmbedder:
    def __init__(self, model_name: str = "bge-m3:latest"):
        self.model_name = model_name
        self.base_url = settings.OLLAMA_BASE_URL
    
    async def embed(self, text: str) -> list[float]:
        """
        Embeds the input text using the Ollama API.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/embed",
                    json={
                        "model": self.model_name,
                        "input": text
                    },
                    timeout=5.0 # Reduced timeout to avoid hanging long on retries
                )
                response.raise_for_status()
                data = response.json()
                # The API returns {"embeddings": [[float, float, ...]]}
                if "embeddings" in data and len(data["embeddings"]) > 0:
                    return data["embeddings"][0]
                raise ValueError("Failed to get embeddings from Ollama API.")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Ollama Embedder unreachable ({e}). Using dummy zero vector fallback for text: {text[:30]}...")
            return [0.0] * settings.EMBEDDING_DIM
