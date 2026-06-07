"""
Refinement LLM —  Ollama (qwen2:1.5b)
- Gọi qua Ollama API giống Qwen-VL
- Tối ưu JSON output
"""

import gc
import json
import re
import requests
import time
from typing import Dict, Any

from ai_pipeline.config import config
from utils.logger import logger, log_model_loading, log_exception


# ── Ollama Configuration ─────────────────────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434"
REFINEMENT_MODEL = "qwen2:1.5b"   # Phiên bản 1.5B Instruct


def _check_ollama_server() -> bool:
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return response.status_code == 200
    except Exception:
        return False


class RefinementLLM:
    """
    Refinement LLM sử dụng Qwen2-1.5B qua Ollama.
    Hoàn toàn không load model vào Python process.
    """

    def __init__(self, model_name: str = None):
        self.model_name = model_name or REFINEMENT_MODEL
        self.base_url = OLLAMA_BASE_URL
        self._validate_server()

    def _validate_server(self):
        """Kiểm tra Ollama server và model"""
        try:
            if not _check_ollama_server():
                logger.error(f"❌ Ollama server chưa chạy tại {self.base_url}")
                raise RuntimeError("Ollama server not available")

            # Kiểm tra model có sẵn
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            available = [m["name"] for m in resp.json().get("models", [])]

            if self.model_name not in available:
                logger.warning(f"Model {self.model_name} chưa có. Hãy chạy: ollama pull {self.model_name}")

            log_model_loading(self.model_name, "loaded")
            logger.info(f"✅ RefinementLLM (Ollama) ready: {self.model_name}")

        except Exception as e:
            log_exception(e, "RefinementLLM._validate_server")
            raise

    def refine_analysis(
        self,
        vision_outputs: Dict[str, str],
        timestamp: float,
        scene_id: int,
        max_new_tokens: int = None,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """Refine vision output thành JSON structure"""
        try:
            prompt = self._build_refinement_prompt(vision_outputs, timestamp, scene_id)

            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_new_tokens or 512,
                    "num_thread": 6,
                },
                "keep_alive": -1   # Giữ model warm
            }

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=90
            )

            if response.status_code != 200:
                logger.error(f"Ollama refinement failed: {response.text}")
                return self._get_fallback_output(vision_outputs, timestamp, scene_id)

            result = response.json()
            generated_text = result.get("response", "").strip()

            return self._parse_json_output(generated_text)

        except Exception as e:
            log_exception(e, "RefinementLLM.refine_analysis")
            return self._get_fallback_output(vision_outputs, timestamp, scene_id)

        finally:
            gc.collect()

    def _build_refinement_prompt(
        self,
        vision_outputs: Dict[str, str],
        timestamp: float,
        scene_id: int,
    ) -> str:
        qwen_text = str(vision_outputs.get("qwen_vl", ""))[:800]

        return (
            f"Timestamp: {timestamp:.1f}s | Scene: {scene_id}\n\n"
            f"Vision Description:\n{qwen_text}\n\n"
            "Hãy chuyển thông tin trên thành JSON theo đúng cấu trúc sau. "
            "Chỉ trả về JSON, không thêm bất kỳ chữ nào khác:\n"
            "{\n"
            '  "summary": "Tóm tắt ngắn gọn bằng 1-2 câu",\n'
            '  "scene": {"type": "", "setting": "", "atmosphere": ""},\n'
            '  "people": [{"clothing": "", "action": "", "emotion": ""}],\n'
            '  "landscape": {"features": [], "weather": "", "time_of_day": "", "lighting": ""},\n'
            '  "camera": {"shot_type": "", "angle": "", "movement": ""},\n'
            '  "colors": {"dominant": [], "mood": ""},\n'
            '  "tags": {"scene_tags": [], "mood_tags": [], "object_tags": []},\n'
            '  "searchable_text": "Từ khóa tìm kiếm chi tiết",\n'
            '  "confidence_score": 0.85\n'
            "}"
        )

    def _parse_json_output(self, text: str) -> Dict[str, Any]:
        text = text.strip()

        # Loại bỏ markdown nếu có
        for fence in ("```json", "```"):
            if text.startswith(fence):
                text = text[len(fence):].strip()
        if text.endswith("```"):
            text = text[:-3].strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Thử extract JSON bằng regex
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
            logger.warning("Không parse được JSON, dùng fallback")
            return self._get_fallback_output({}, 0.0, 0)

    def _get_fallback_output(self, vision_outputs: Dict, timestamp: float, scene_id: int) -> Dict[str, Any]:
        qwen_text = str(vision_outputs.get("qwen_vl", ""))[:400]
        return {
            "summary": qwen_text[:250],
            "scene": {"type": "unknown", "setting": "", "atmosphere": ""},
            "people": [],
            "landscape": {"features": [], "weather": "", "time_of_day": "", "lighting": ""},
            "camera": {"shot_type": "", "angle": "", "movement": ""},
            "colors": {"dominant": [], "mood": ""},
            "tags": {"scene_tags": [], "mood_tags": [], "object_tags": []},
            "searchable_text": qwen_text[:350],
            "confidence_score": 0.6,
        }

    def unload(self):
        """Với Ollama thì chỉ dọn reference và GC"""
        logger.info(f"RefinementLLM ({self.model_name}) context cleared (Ollama managed)")
        gc.collect()


def create_refinement_llm() -> RefinementLLM:
    return RefinementLLM()