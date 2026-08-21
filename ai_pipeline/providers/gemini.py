import os
import logging
from pathlib import Path
from typing import List, Optional
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

import google.generativeai as genai
from .base import TextEmbedder, VisionProvider

logger = logging.getLogger(__name__)

class GeminiProvider(VisionProvider, TextEmbedder):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        genai.configure(api_key=self.api_key)
        self.embedding_dim = 768
        
        # We use gemini-1.5-flash for fast vision/multimodal tasks
        self.vision_model = genai.GenerativeModel('gemini-1.5-flash')
        # We use text-embedding-004 for embeddings
        self.embedding_model = 'models/text-embedding-004'

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def caption_keyframe(self, image_path: Path, prompt: Optional[str] = None) -> str:
        """Use Gemini 1.5 Flash to caption an image frame."""
        import PIL.Image
        img = PIL.Image.open(image_path)
        
        default_prompt = (
            "Describe exactly what is happening in this image. "
            "Focus on actions, objects, setting, and text visible in the frame. "
            "Keep it concise but detailed."
        )
        final_prompt = prompt or default_prompt
        
        response = self.vision_model.generate_content([final_prompt, img])
        return response.text.strip()

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def embed_text(self, text: str) -> List[float]:
        result = genai.embed_content(
            model=self.embedding_model,
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        result = genai.embed_content(
            model=self.embedding_model,
            content=texts,
            task_type="retrieval_document"
        )
        return result['embedding']
