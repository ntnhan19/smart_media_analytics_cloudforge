"""
Refinement LLM — Semantic Search Optimized for Video Editors (qwen2:1.5b)
Mục tiêu: Tạo metadata chất lượng cao giúp editor tìm lại video dễ dàng sau nhiều tháng
- Prompt tối ưu cho model nhỏ
- Chống drift tiếng Anh cực mạnh
- Output tương thích với SceneAnalysisContract
"""

import gc
import json
import os
import re
import requests
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

try:
    import boto3
except ImportError:
    pass

from ai_pipeline.config import config
from utils.logger import logger, log_model_loading, log_exception


# =============================================================================
# Helpers
# =============================================================================

def _sanitize_whisper_text(text: str) -> str:
    if not text or not text.strip():
        return ""
    cleaned = re.sub(r"\[.*?\]|\(.*?\)", "", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:480]


def _sanitize_vision_caption(caption: str) -> str:
    if not caption or not caption.strip():
        return ""
    cleaned = re.sub(r"[*_`#>\-]", " ", caption)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:300]


def _is_likely_english(text: str) -> bool:
    if not text or len(text) < 15:
        return False
    if re.search(r"[ăâđêôơưáàảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]", text.lower()):
        return False
    alpha = [c for c in text if c.isalpha()]
    if not alpha:
        return False
    ascii_ratio = sum(1 for c in alpha if ord(c) < 128) / len(alpha)
    return ascii_ratio > 0.73


def _contains_english_rubbish(text: str) -> bool:
    if not text:
        return False
    lowered = text.lower()
    rubbish = [
        "main subjects", "visible objects", "scene type", "action:", 
        "location cues", "shot type", "camera movement", "dominant color"
    ]
    return any(p in lowered for p in rubbish)


# =============================================================================
# JSON Repair
# =============================================================================

def _close_open_json(text: str) -> str:
    stack = []
    in_string = False
    escape = False
    result = []
    for ch in text:
        result.append(ch)
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in ("{", "["):
            stack.append(ch)
        elif ch in ("}", "]"):
            if stack and stack[-1] == ("{" if ch == "}" else "["):
                stack.pop()
    out = "".join(result)
    if in_string:
        out += '"'
    for bracket in reversed(stack):
        out += "}" if bracket == "{" else "]"
    return out


def _repair_json(raw: str) -> Optional[str]:
    if not raw:
        return None
    text = re.sub(r"```json?|```", "", raw).strip()
    if text in ("{}", "{ }", ""):
        return None
    rep = re.search(r"(.{10,})\1{2,}", text)
    if rep:
        text = text[:rep.start()]
    text = _close_open_json(text)
    if not text.startswith("{"):
        match = re.search(r"\{.*", text, re.DOTALL)
        if match:
            text = _close_open_json(match.group())
        else:
            return None
    return text


# =============================================================================
# Base Abstraction
# =============================================================================

class BaseRefinementLLM(ABC):
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


# =============================================================================
# Ollama Implementation
# =============================================================================

class OllamaRefinementLLM(BaseRefinementLLM):
    def __init__(self, model_name: str = None):
        self.base_url = getattr(config, "OLLAMA_BASE_URL", "http://host.docker.internal:11434")
        self.model_name = model_name or "qwen2:1.5b"
        self._validate_server()

    def _validate_server(self):
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if resp.status_code != 200:
                raise RuntimeError("Ollama not ready")
            models = [m["name"] for m in resp.json().get("models", [])]
            if self.model_name not in models:
                logger.warning(f"Model {self.model_name} not found. Run: ollama pull {self.model_name}")
            log_model_loading(self.model_name, "loaded")
            logger.info(f"✅ RefinementLLM ready: {self.model_name} @ {self.base_url}")
        except Exception as e:
            log_exception(e, "OllamaRefinementLLM._validate_server")
            raise

    def refine_analysis(
        self,
        vision_outputs: Dict[str, str],
        timestamp: float,
        scene_id: int,
        transcript_snippet: str = "",
    ) -> Dict[str, Any]:
        try:
            prompt = self._build_optimized_prompt(vision_outputs, timestamp, scene_id, transcript_snippet)

            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.1,
                    "num_predict": 512,
                    "num_ctx": 4096,
                    "repeat_penalty": 1.1,
                    "stop": ["<|im_end|>", "</s>"],
                },
                "keep_alive": -1,
            }

            response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=90)

            if response.status_code != 200:
                logger.error(f"Ollama error scene {scene_id}")
                return self._get_fallback_output(vision_outputs, timestamp, scene_id, transcript_snippet)

            text = response.json().get("response", "").strip()
            return self._parse_and_validate(text, vision_outputs, timestamp, scene_id, transcript_snippet)

        except Exception as e:
            log_exception(e, "OllamaRefinementLLM.refine_analysis")
            return self._get_fallback_output(vision_outputs, timestamp, scene_id, transcript_snippet)
        finally:
            gc.collect()

    def _build_optimized_prompt(self, vision_outputs: Dict, timestamp: float, scene_id: int, transcript_snippet: str) -> str:
        vision_text = _sanitize_vision_caption(str(vision_outputs.get("qwen_vl", "")))
        audio_text = _sanitize_whisper_text(transcript_snippet)

        system_prompt = (
            "Bạn là AI tạo metadata video chuyên nghiệp. Hãy dựa vào thông tin 'Hình ảnh' và 'Lời thoại' để sinh dữ liệu.\n"
            "BẮT BUỘC TRẢ VỀ ĐỊNH DẠNG JSON PHẲNG VỚI CÁC KEY SAU (TẤT CẢ PHẢI LÀ TIẾNG VIỆT):\n"
            '- "summary": Viết 1 câu tiếng Việt ngắn gọn, mô tả chính xác hành động hoặc nội dung phân cảnh.\n'
            '- "scene_tags": Mảng chứa từ 3 đến 5 từ khóa viết thường, có dấu, phân loại nội dung (ví dụ: ["xe hơi", "đường phố", "ban ngày"]).\n'
            '- "searchable_text": Câu summary được viết lại bằng tiếng Việt không dấu (ví dụ: "phan canh co nguoi noi chuyen").\n\n'
            "Chỉ trả về JSON hợp lệ. Không viết thêm lời thoại hay giải thích."
        )

        audio_section = f"Lời thoại: {audio_text}\n" if audio_text else ""
        vision_section = f"Hình ảnh: {vision_text}\n" if vision_text else "Hình ảnh: Không có thông tin\n"

        user_prompt = (
            f"--- DỮ LIỆU ĐẦU VÀO ---\n"
            f"{vision_section}"
            f"{audio_section}\n"
            f"--- KẾT QUẢ JSON ---\n"
        )

        return (
            f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
            f"<|im_start|>user\n{user_prompt}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )

    def _parse_and_validate(self, text: str, vision_outputs: Dict, timestamp: float, scene_id: int, transcript_snippet: str) -> Dict[str, Any]:
        repaired = _repair_json(text)
        if not repaired:
            return self._get_fallback_output(vision_outputs, timestamp, scene_id, transcript_snippet)

        try:
            parsed = json.loads(repaired)
            return self._validate_output(parsed, vision_outputs, timestamp, scene_id, transcript_snippet)
        except json.JSONDecodeError:
            logger.warning(f"Scene {scene_id}: JSON parse failed")
            return self._get_fallback_output(vision_outputs, timestamp, scene_id, transcript_snippet)

    def _validate_output(self, parsed: Dict, vision_outputs: Dict, timestamp: float, scene_id: int, transcript_snippet: str) -> Dict[str, Any]:
        if not isinstance(parsed, dict):
            return self._get_fallback_output(vision_outputs, timestamp, scene_id, transcript_snippet)

        summary = str(parsed.get("summary", "")).strip()
        if not summary:
            return self._get_fallback_output(vision_outputs, timestamp, scene_id, transcript_snippet)

        scene_tags = parsed.get("scene_tags", parsed.get("tags", {}).get("scene_tags", ["video"]))
        if isinstance(scene_tags, list):
            scene_tags = [str(t).strip().lower() for t in scene_tags if str(t).strip()][:6]
        else:
            scene_tags = ["video"]

        searchable_text = str(parsed.get("searchable_text", summary)).strip()

        return {
            "summary": summary[:420],
            "tags": {"scene_tags": scene_tags},
            "searchable_text": searchable_text[:750],
        }

    def _get_fallback_output(self, vision_outputs, timestamp, scene_id, transcript_snippet=""):
        audio = _sanitize_whisper_text(transcript_snippet)
        summary = f"Phân cảnh video tại {timestamp:.0f} giây"
        if audio:
            summary = f"Phân cảnh có lời thoại: {audio[:200]}"

        return {
            "summary": summary,
            "tags": {"scene_tags": ["video"]},
            "searchable_text": summary,
        }

    def unload(self):
        logger.info(f"RefinementLLM ({self.model_name}) unloaded")
        gc.collect()

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


# =============================================================================
# Bedrock Implementation
# =============================================================================

class BedrockRefinementLLM(BaseRefinementLLM):
    def __init__(self, model_name: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"):
        self.model_name = model_name
        from botocore.config import Config
        config = Config(retries={"max_attempts": 1, "mode": "standard"})
        self.client = boto3.client("bedrock-runtime", config=config)
        logger.info(f"☁️ BedrockRefinementLLM initialized with {model_name}")

    def refine_analysis(self, vision_outputs, timestamp, scene_id, transcript_snippet=""):
        vision_text = str(vision_outputs.get("qwen_vl", "")).strip()
        audio_text = str(transcript_snippet).strip()

        prompt = (
            "Bạn là AI tạo metadata video chuyên nghiệp. Hãy dựa vào thông tin 'Hình ảnh' và 'Lời thoại' để sinh dữ liệu.\n"
            f"Hình ảnh: {vision_text}\n"
            f"Lời thoại: {audio_text}\n\n"
            "BẮT BUỘC TRẢ VỀ ĐỊNH DẠNG JSON PHẲNG VỚI CÁC KEY SAU (TẤT CẢ PHẢI LÀ TIẾNG VIỆT):\n"
            '- "summary": Viết 1 câu tiếng Việt ngắn gọn mô tả phân cảnh.\n'
            '- "scene_tags": Mảng chứa từ 3 đến 5 từ khóa (ví dụ: ["xe hơi", "đường phố"]).\n'
            '- "searchable_text": Câu summary viết lại tiếng Việt không dấu.\n'
            "Chỉ trả về JSON hợp lệ."
        )

        try:
            response = self.client.invoke_model(
                modelId=self.model_name,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 512,
                    "messages": [{"role": "user", "content": prompt}]
                }),
                contentType="application/json",
                accept="application/json"
            )
            result = json.loads(response['body'].read().decode('utf-8'))
            text = result.get('content', [{}])[0].get('text', '')
            parsed = json.loads(_repair_json(text))
            
            summary = str(parsed.get("summary", "")).strip()
            scene_tags = parsed.get("scene_tags", ["video"])
            if not isinstance(scene_tags, list): scene_tags = ["video"]
            searchable_text = str(parsed.get("searchable_text", summary)).strip()
            return {
                "summary": summary[:420] if summary else f"Phân cảnh {scene_id}",
                "tags": {"scene_tags": [str(t) for t in scene_tags[:6]]},
                "searchable_text": searchable_text[:750],
            }
        except Exception as e:
            logger.error(f"Bedrock refine error scene {scene_id}: {e}")
            return {
                "summary": f"Phân cảnh {scene_id} tại {timestamp:.1f} giây",
                "tags": {"scene_tags": ["video"]},
                "searchable_text": f"phan canh video {scene_id}",
            }

    def generate_asset_insights(self, aggregated_text: str) -> Dict[str, Any]:
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
            response = self.client.invoke_model(
                modelId=self.model_name,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": prompt}]
                }),
                contentType="application/json",
                accept="application/json"
            )
            result = json.loads(response['body'].read().decode('utf-8'))
            text = result.get('content', [{}])[0].get('text', '')
            parsed = json.loads(_repair_json(text))
            
            return {
                "summary": parsed.get("summary", "Tổng hợp nội dung video."),
                "moods": parsed.get("moods", ["unknown"]),
                "objects": parsed.get("objects", ["video"]),
                "best_for": parsed.get("best_for", ["general"])
            }
        except Exception as e:
            logger.error(f"Bedrock asset insights error: {e}")
            return {
                "summary": "Video tổng hợp từ các phân cảnh.",
                "moods": ["general"],
                "objects": ["video"],
                "best_for": ["general"]
            }

    def unload(self):
        pass


# =============================================================================
# Factory
# =============================================================================

def create_refinement_llm() -> BaseRefinementLLM:
    provider = os.getenv("AI_PROVIDER", "local").strip().lower()
    if provider == "aws":
        return BedrockRefinementLLM()
    return OllamaRefinementLLM()