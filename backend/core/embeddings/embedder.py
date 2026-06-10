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
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/embed",
                json={
                    "model": self.model_name,
                    "input": text
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            # The API returns {"embeddings": [[float, float, ...]]}
            if "embeddings" in data and len(data["embeddings"]) > 0:
                return data["embeddings"][0]
            raise ValueError("Failed to get embeddings from Ollama API.")
