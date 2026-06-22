"""
Refinement LLM — Ollama (qwen2:1.5b) & Cloud-Ready Abstraction
- Tự động chuyển đổi cấu hình mạng động dựa trên môi trường Docker/Local.
- Hỗ trợ switch cấu hình linh hoạt qua biến môi trường AI_PROVIDER.
- Tối ưu JSON output chạy trên CPU.
"""

import gc
import json
import os
import re
import requests
import time
from abc import ABC, abstractmethod
from typing import Dict, Any

from ai_pipeline.config import config
from utils.logger import logger, log_model_loading, log_exception


# ── Base Abstraction Class (Task 7) ─────────────────────────────────────────
class BaseRefinementLLM(ABC):
    """Giao diện nền tảng (Interface) chuẩn bị cho việc tích hợp AWS Bedrock"""
    
    @abstractmethod
    def refine_analysis(
        self,
        vision_outputs: Dict[str, str],
        timestamp: float,
        scene_id: int,
        transcript_snippet: str = "",
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def generate_asset_insights(self, aggregated_text: str) -> Dict[str, Any]:
        """Tổng hợp Insights cấp độ Asset từ text caption và transcript."""
        pass

    @abstractmethod
    def unload(self):
        pass


# ── Ollama Implementation ───────────────────────────────────────────────────
class OllamaRefinementLLM(BaseRefinementLLM):
    """Thực thi kết nối cục bộ qua Ollama API"""

    def __init__(self, model_name: str = None):
        # ✨ SỬA LỖI MẠNG: Ưu tiên lấy URL từ config hệ thống (chứa host.docker.internal), tránh gán cứng localhost
        self.base_url = getattr(config, "OLLAMA_BASE_URL", "http://host.docker.internal:11434")
        self.model_name = model_name or "qwen2:1.5b"
        self._validate_server()

    def _validate_server(self):
        """Kiểm tra Ollama server và model"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if response.status_code != 200:
                raise RuntimeError("Status code not 200")
                
            available = [m["name"] for m in response.json().get("models", [])]
            if self.model_name not in available:
                logger.warning(f"⚠️ Model {self.model_name} chưa có local. Hãy chạy: ollama pull {self.model_name}")

            log_model_loading(self.model_name, "loaded")
            logger.info(f"✅ RefinementLLM (Ollama) ready: {self.model_name} tại {self.base_url}")
        except Exception as e:
            logger.error(f"❌ Ollama server chưa chạy tại địa chỉ: {self.base_url}")
            log_exception(e, "OllamaRefinementLLM._validate_server")
            raise RuntimeError(f"Ollama server not available at {self.base_url}") from e

    def refine_analysis(
        self,
        vision_outputs: Dict[str, str],
        timestamp: float,
        scene_id: int,
        transcript_snippet: str = "",
        max_new_tokens: int = 350,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """Refine vision & audio output thành cấu trúc JSON chuẩn"""
        try:
            prompt = self._build_refinement_prompt(vision_outputs, timestamp, scene_id, transcript_snippet)

            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "format": "json", # Ép Ollama luôn luôn xuất ra JSON hợp lệ
                "options": {
                    "temperature": temperature,
                    "num_predict": max_new_tokens, 
                    "num_thread": 6,
                    "num_ctx": 2048, # Giới hạn ngữ cảnh tăng tốc cho CPU
                },
                "keep_alive": -1
            }

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60
            )

            if response.status_code != 200:
                logger.error(f"Ollama refinement failed: {response.text}")
                return self._get_fallback_output(vision_outputs, timestamp, scene_id, transcript_snippet)

            result = response.json()
            generated_text = result.get("response", "").strip()
            return self._parse_json_output(generated_text, vision_outputs, timestamp, scene_id, transcript_snippet)

        except Exception as e:
            log_exception(e, "OllamaRefinementLLM.refine_analysis")
            return self._get_fallback_output(vision_outputs, timestamp, scene_id, transcript_snippet)
        finally:
            gc.collect()

    def _build_refinement_prompt(
        self,
        vision_outputs: Dict[str, str],
        timestamp: float,
        scene_id: int,
        transcript_snippet: str = "",
    ) -> str:
        qwen_text = str(vision_outputs.get("qwen_vl", ""))[:800]
        audio_text = str(transcript_snippet).strip() if transcript_snippet else "Không có giọng nói"

        return (
            f"Hãy phân tích bối cảnh phân cảnh sau đây để xuất ra cấu trúc JSON chi tiết.\n\n"
            f"Thông tin phân cảnh:\n"
            f"- Thời gian: {timestamp:.1f}s | ID Phân cảnh: {scene_id}\n"
            f"- Lời thoại (Từ Whisper): \"{audio_text}\"\n"
            f"- Mô tả hình ảnh (Từ Vision Model): \"{qwen_text}\"\n\n"
            "Yêu cầu xuất ra một chuỗi JSON chuẩn (không kèm markdown block) khớp 100% định dạng mẫu này:\n"
            "{\n"
            '  "summary": "Tóm tắt kết hợp cả nội dung lời thoại và hình ảnh bằng 1-2 câu tiếng Việt mượt mà",\n'
            '  "scene": {"type": "Video âm nhạc/Vlog/Phim/Bản tin...", "setting": "Trong nhà/Ngoài trời", "atmosphere": "Vui vẻ/Sâu lắng/Hồi hộp"},\n'
            '  "people": [{"clothing": "Mô tả quần áo", "action": "Hành động của nhân vật", "emotion": "Cảm xúc"}],\n'
            '  "landscape": {"features": [], "weather": "Nắng/Mưa/Bình thường", "time_of_day": "Ngày/Đêm", "lighting": "Sáng/Tối"},\n'
            '  "camera": {"shot_type": "Cận cảnh/Toàn cảnh", "angle": "Ngang mắt/Góc cao/Góc thấp", "movement": "Đứng yên/Lướt qua/Zoom"},\n'
            '  "colors": {"dominant": ["Màu chủ đạo"], "mood": "Tông màu chung"},\n'
            '  "tags": {"scene_tags": ["tag_bối_cảnh"], "mood_tags": ["tag_cảm_xúc"], "object_tags": ["tag_vật_thể"]},\n'
            '  "searchable_text": "Chuỗi từ khóa tìm kiếm tiếng Việt tổng hợp sâu sắc",\n'
            '  "confidence_score": 0.90\n'
            "}"
        )

    def generate_asset_insights(self, aggregated_text: str, max_new_tokens: int = 500, temperature: float = 0.2) -> Dict[str, Any]:
        """Tổng hợp AI Insights (Summary, Moods, Objects, Best For) cho toàn bộ Asset"""
        prompt = (
            "Dựa trên các phân cảnh và lời thoại sau đây của một video, hãy tổng hợp thông tin chung "
            "về toàn bộ video này và xuất ra chuẩn JSON (không kèm markdown block).\n\n"
            f"Nội dung:\n{aggregated_text[:3000]}\n\n"
            "Yêu cầu định dạng JSON:\n"
            "{\n"
            '  "summary": "Tóm tắt ngắn gọn 2-3 câu về nội dung chính của video",\n'
            '  "moods": ["Vui vẻ", "Hồi hộp", ...],\n'
            '  "objects": ["Xe hơi", "Biển", "Điện thoại", ...],\n'
            '  "best_for": ["Vlog", "Quảng cáo", "Tiktok", ...]\n'
            "}"
        )
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": temperature,
                    "num_predict": max_new_tokens,
                    "num_thread": 6,
                    "num_ctx": 4096,
                },
                "keep_alive": -1
            }
            response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=90)
            if response.status_code != 200:
                logger.error(f"Ollama asset insights failed: {response.text}")
                return self._get_fallback_asset_insights(aggregated_text)
            
            result = response.json()
            generated_text = result.get("response", "").strip()
            return self._parse_json_asset_insights(generated_text, aggregated_text)
        except Exception as e:
            log_exception(e, "OllamaRefinementLLM.generate_asset_insights")
            return self._get_fallback_asset_insights(aggregated_text)
        finally:
            gc.collect()

    def _parse_json_asset_insights(self, text: str, fallback_text: str) -> Dict[str, Any]:
        text = text.strip()
        for fence in ("```json", "```"):
            if text.startswith(fence):
                text = text[len(fence):].strip()
        if text.endswith("```"):
            text = text[:-3].strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
            return self._get_fallback_asset_insights(fallback_text)

    def _get_fallback_asset_insights(self, text: str) -> Dict[str, Any]:
        return {
            "summary": "Không thể tổng hợp tự động do lỗi hệ thống.",
            "moods": ["unknown"],
            "objects": [],
            "best_for": ["unknown"]
        }

    def _parse_json_output(self, text: str, vision_outputs: Dict, timestamp: float, scene_id: int, transcript_snippet: str) -> Dict[str, Any]:
        text = text.strip()
        for fence in ("```json", "```"):
            if text.startswith(fence):
                text = text[len(fence):].strip()
        if text.endswith("```"):
            text = text[:-3].strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
            return self._get_fallback_output(vision_outputs, timestamp, scene_id, transcript_snippet)

    def _get_fallback_output(self, vision_outputs: Dict, timestamp: float, scene_id: int, transcript_snippet: str = "") -> Dict[str, Any]:
        qwen_text = str(vision_outputs.get("qwen_vl", ""))[:400]
        audio_text = str(transcript_snippet)[:200]
        summary = f"Lời thoại: {audio_text}. Hình ảnh: {qwen_text}"[:250]
        return {
            "summary": summary,
            "scene": {"type": "unknown", "setting": "unknown", "atmosphere": "unknown"},
            "people": [],
            "landscape": {"features": [], "weather": "unknown", "time_of_day": "unknown", "lighting": "unknown"},
            "camera": {"shot_type": "unknown", "angle": "unknown", "movement": "unknown"},
            "colors": {"dominant": [], "mood": "unknown"},
            "tags": {"scene_tags": [], "mood_tags": [], "object_tags": []},
            "searchable_text": f"{audio_text} {qwen_text}"[:350],
            "confidence_score": 0.5,
        }

    def unload(self):
        logger.info(f"RefinementLLM ({self.model_name}) context cleared")
        gc.collect()


# ── AWS Bedrock Stub Implementation (Task 7 Cloud-Ready) ────────────────────
class BedrockRefinementLLM(BaseRefinementLLM):
    """Khung class placeholder sẵn sàng tích hợp với AWS Bedrock SDK khi lên Cloud"""
    
    def __init__(self, model_name: str = "amazon.titan-text-express-v1"):
        self.model_name = model_name
        logger.info(f"☁️ BedrockRefinementLLM Stub initialized with model: {self.model_name}")

    def refine_analysis(self, vision_outputs: Dict[str, str], timestamp: float, scene_id: int, transcript_snippet: str = "") -> Dict[str, Any]:
        # Giả lập phản hồi (Mock response) chuẩn cấu hình JSON của Local để luồng test chạy qua mà không lỗi gãy
        qwen_text = str(vision_outputs.get("qwen_vl", ""))[:200]
        return {
            "summary": f"[AWS Bedrock Cloud Stub Summary] {qwen_text}",
            "scene": {"type": "Vlog", "setting": "Cloud", "atmosphere": "stable"},
            "people": [],
            "landscape": {"features": [], "weather": "clear", "time_of_day": "day", "lighting": "bright"},
            "camera": {"shot_type": "medium", "angle": "eye-level", "movement": "static"},
            "colors": {"dominant": ["blue"], "mood": "neutral"},
            "tags": {"scene_tags": ["cloud_stub"], "mood_tags": ["stable"], "object_tags": []},
            "searchable_text": "AWS Bedrock cloud test placeholder",
            "confidence_score": 0.95
        }

    def generate_asset_insights(self, aggregated_text: str) -> Dict[str, Any]:
        return {
            "summary": "[AWS Stub] Video tổng hợp từ các phân cảnh.",
            "moods": ["aws-stub-mood"],
            "objects": ["aws-object-1"],
            "best_for": ["aws-stub-tag"]
        }

    def unload(self):
        pass


# ── Provider Switch Factory (Task 7) ────────────────────────────────────────
def create_refinement_llm() -> BaseRefinementLLM:
    """Bộ chuyển mạch linh hoạt dựa trên biến môi trường AI_PROVIDER"""
    provider = os.getenv("AI_PROVIDER", "local").strip().lower()
    if provider == "aws":
        return BedrockRefinementLLM()
    return OllamaRefinementLLM()