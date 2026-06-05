"""
Vision Models — Ollama-based (qwen2.5-vl:3b)
- Qwen2.5-VL-3B via local Ollama server
- Tối ưu tốc độ: JPEG + resize 448px + keep_alive
"""

import gc
import time
import base64
import requests
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from PIL import Image
import io
import numpy as np

from ai_pipeline.config import config
from utils.logger import logger, log_model_loading, log_exception


# ── Ollama Configuration ─────────────────────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434"
QWEN_VL_MODEL = "qwen2.5vl:3b"
FLORENCE_MODEL_ALT = "qwen2.5vl:3b"


def _check_ollama_server() -> bool:
    """Check if Ollama server is running."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def _free_vram():
    """Giải phóng RAM sau mỗi inference."""
    gc.collect()


def _resize_image(image: Image.Image, max_size: int = 448) -> Image.Image:
    """Ép cứng kích thước vàng 448px để giảm dung lượng payload."""
    w, h = image.size
    if max(w, h) <= max_size:
        return image
    scale = max_size / max(w, h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    return image.resize((new_w, new_h), Image.Resampling.LANCZOS)


def _image_to_base64(image: Image.Image) -> str:
    """Chuyển sang JPEG quality=85 để giảm kích thước base64 mạnh."""
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=85)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


# ── Qwen2.5-VL-3B (Ollama) ─────────────────────────────────────────────────────

class QwenVLModel:
    def __init__(self, model_name: str = None, device: str = None):
        self.model_name = model_name or QWEN_VL_MODEL
        self.base_url = OLLAMA_BASE_URL
        self._validate_server()

    def _validate_server(self):
        try:
            if not _check_ollama_server():
                logger.error(f"Ollama server not running at {self.base_url}")
                raise RuntimeError("Ollama server not available")

            response = requests.get(f"{self.base_url}/api/tags")
            available_models = [m["name"] for m in response.json().get("models", [])]

            if self.model_name not in available_models:
                logger.warning(f"Model {self.model_name} not found. Run: ollama pull {self.model_name}")

            log_model_loading(self.model_name, "loaded")
            logger.info(f"Qwen-VL (Ollama) ready - keep_alive enabled")

        except Exception as e:
            log_exception(e, "QwenVLModel._validate_server")
            raise

    def analyze_image(
        self,
        image: Image.Image,
        prompt: str = None,
        max_new_tokens: int = None,
        temperature: float = 0.3,
    ) -> str:
        try:
            image = _resize_image(image)
            if prompt is None:
                prompt = self._get_default_prompt()

            image_base64 = _image_to_base64(image)

            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_new_tokens or config.model.max_new_tokens_vision,
                    "num_thread": 6,           # Thêm dòng này
                },
                "keep_alive": -1
            }

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=300
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama request failed: {response.text}")
                return ""

            result = response.json()
            return result.get("response", "").strip()

        except Exception as e:
            log_exception(e, "QwenVLModel.analyze_image")
            return ""
        finally:
            _free_vram()

    def _get_default_prompt(self) -> str:
        return (
            "Describe this video frame concisely covering: "
            "1) Scene type and setting 2) People (appearance, action) "
            "3) Lighting and time of day 4) Camera angle 5) Mood and colors "
            "6) Key objects. Be specific. Max 150 words."
        )

    def batch_analyze_images(
        self,
        images: List[Image.Image],
        prompts: List[str] = None,
        batch_size: int = 1,
    ) -> List[str]:
        results = []
        if prompts is None:
            prompts = [self._get_default_prompt()] * len(images)

        for img, prompt in zip(images, prompts):
            result = self.analyze_image(img, prompt)
            results.append(result)
            _free_vram()

        return results


# ── Florence-2 (Adapter qua Qwen) ────────────────────────────────────────────

class Florence2Model:
    def __init__(self, model_name: str = None, device: str = None):
        self.model_name = FLORENCE_MODEL_ALT
        self.base_url = OLLAMA_BASE_URL
        self._validate_server()

    def _validate_server(self):
        try:
            if not _check_ollama_server():
                raise RuntimeError("Ollama server not available")
            log_model_loading(self.model_name, "loaded")
        except Exception as e:
            log_exception(e, "Florence2Model._validate_server")
            raise

    def _call_ollama(
        self,
        image: Image.Image,
        prompt: str,
        max_tokens: int = 512,
    ) -> str:
        try:
            image = _resize_image(image)
            image_base64 = _image_to_base64(image)

            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": max_tokens,
                    "num_thread": 6,        
                },
                "keep_alive": -1
            }

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120
            )
            
            if response.status_code != 200:
                return ""
            result = response.json()
            return result.get("response", "").strip()

        except Exception as e:
            log_exception(e, "Florence2Model._call_ollama")
            return ""
        finally:
            _free_vram()

    def detect_objects(self, image: Image.Image) -> Dict[str, Any]:
        prompt = "List all objects and entities visible in this image with location and size."
        response = self._call_ollama(image, prompt)
        return {"objects_detected": bool(response), "description": response, "raw_response": response}

    def dense_caption(self, image: Image.Image) -> Dict[str, Any]:
        prompt = "Provide dense captions for different regions of this image."
        response = self._call_ollama(image, prompt)
        return {"captions_available": bool(response), "captions": response, "raw_response": response}

    def caption_to_phrase_grounding(self, image: Image.Image, caption: str = None) -> Dict[str, Any]:
        prompt = f"For the phrase: '{caption or 'image'}', describe locations of main elements."
        response = self._call_ollama(image, prompt)
        return {"grounding_available": bool(response), "grounding": response, "raw_response": response}


# ── ModelManager ─────────────────────────────────────────────────────────────

class ModelManager:
    def __init__(self):
        self.qwen_vl: Optional[QwenVLModel] = None
        self.florence: Optional[Florence2Model] = None
        self.loaded_models: set = set()

    def load_qwen_vl(self):
        if self.qwen_vl is None:
            try:
                self.qwen_vl = QwenVLModel()
                self.loaded_models.add("qwen_vl")
            except Exception as e:
                logger.error(f"Failed to load Qwen-VL: {e}")

    def load_florence(self):
        if self.florence is None:
            try:
                self.florence = Florence2Model()
                self.loaded_models.add("florence")
            except Exception as e:
                logger.error(f"Failed to load Florence: {e}")

    def load_models_for_mode(self, mode: str):
        mode_config = config.get_processing_mode_config(mode)
        if mode_config.get("use_qwen_vl"):
            self.load_qwen_vl()
        if mode_config.get("use_florence"):
            self.load_florence()
        logger.info(f"Vision models loaded for '{mode}': {self.loaded_models}")

    def unload_all(self):
        self.qwen_vl = None
        self.florence = None
        self.loaded_models.clear()
        _free_vram()
        logger.info("All vision model wrappers unloaded")