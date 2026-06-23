# -*- coding: utf-8 -*-
"""
Vision Models — Semantic Visual Signal Extractor for Editor Search
-----------------------------------------------------------------
Mục tiêu:
- KHÔNG tạo caption cuối cùng cho user.
- Chỉ trích xuất tín hiệu thị giác có cấu trúc (JSON) để phục vụ tìm kiếm.
- Đôi mắt chính của hệ thống: Sử dụng qwen2.5vl:3b chạy qua Ollama Local.
"""

from __future__ import annotations

import base64
import gc
import io
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import requests
from PIL import Image

from ai_pipeline.config import config
from utils.logger import logger, log_exception, log_model_loading


# =============================================================================
# Config
# =============================================================================

@dataclass
class VisionConfig:
    base_url: str = getattr(config, "OLLAMA_BASE_URL", "http://localhost:11434")
    model_name: str = "qwen2.5vl:3b"

    request_timeout_sec: int = 120
    health_timeout_sec: int = 3

    # Kích thước vàng tối ưu tốc độ xử lý cho Qwen-VL
    max_image_size: int = 448  
    jpeg_quality: int = 85

    # Cấu hình retry
    max_retries: int = 2
    retry_delay_sec: float = 1.2

    # Tham số sinh JSON ổn định
    temperature: float = 0.1
    num_predict: int = 200
    num_ctx: int = 2048
    num_thread: int = 6


VISION_CONFIG = VisionConfig()


# =============================================================================
# Helpers
# =============================================================================

def _check_ollama_server(base_url: str) -> bool:
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=VISION_CONFIG.health_timeout_sec)
        return resp.status_code == 200
    except Exception:
        return False


def _free_memory() -> None:
    gc.collect()


def _resize_image(image: Image.Image, max_size: int) -> Image.Image:
    w, h = image.size
    if max(w, h) <= max_size:
        return image
    scale = max_size / max(w, h)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    return image.resize((new_w, new_h), Image.Resampling.LANCZOS)


def _image_to_base64(image: Image.Image, jpeg_quality: int) -> str:
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=jpeg_quality, optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _clean_line(text: str) -> str:
    if not text:
        return ""
    text = text.replace("*", " ").replace("#", " ").replace("`", " ")
    text = re.sub(r"\s+", " ", text).strip(" -:;,.")
    return text.strip()


def _safe_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        out = []
        for x in value:
            s = _clean_line(str(x))
            if s:
                out.append(s)
        return out
    if isinstance(value, str):
        parts = re.split(r"[,\n;/|]+", value)
        return [p.strip() for p in parts if p.strip()]
    return []


def _dedupe_keep_order(items: Sequence[str], limit: int = 8) -> List[str]:
    seen = set()
    out = []
    for item in items:
        key = item.lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item.strip())
        if len(out) >= limit:
            break
    return out


def _repair_json(raw: str) -> Optional[str]:
    """Tự động vá chuỗi JSON lỗi nhẹ phát sinh từ Ollama."""
    if not raw or not raw.strip():
        return None

    text = raw.strip()
    text = re.sub(r"```json|
```", "", text, flags=re.IGNORECASE).strip()

    if not text.startswith("{"):
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if m:
            text = m.group(0)

    if not text.startswith("{"):
        return None

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
        if ch in "{[":
            stack.append(ch)
        elif ch == "}":
            if stack and stack[-1] == "{":
                stack.pop()
        elif ch == "]":
            if stack and stack[-1] == "[":
                stack.pop()

    repaired = "".join(result)
    if in_string:
        repaired += '"'

    for opener in reversed(stack):
        repaired += "}" if opener == "{" else "]"

    return repaired.strip()


# =============================================================================
# Vision Output Contract
# =============================================================================

@dataclass
class VisionSceneSignals:
    """Tín hiệu thị giác có cấu trúc dùng làm đầu vào cho bộ não Refinement LLM."""
    shot_type: str = ""
    main_subjects: List[str] = None
    actions: List[str] = None
    setting: str = ""
    visual_cues: List[str] = None
    raw_caption: str = ""

    def __post_init__(self):
        self.main_subjects = self.main_subjects or []
        self.actions = self.actions or []
        self.visual_cues = self.visual_cues or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "shot_type": self.shot_type,
            "main_subjects": self.main_subjects,
            "actions": self.actions,
            "setting": self.setting,
            "visual_cues": self.visual_cues,
            "raw_caption": self.raw_caption,
        }

    def to_search_hint_text(self) -> str:
        parts = []
        if self.shot_type: parts.append(f"Cỡ cảnh: {self.shot_type}")
        if self.main_subjects: parts.append("Chủ thể: " + ", ".join(self.main_subjects))
        if self.actions: parts.append("Hành động: " + ", ".join(self.actions))
        if self.setting: parts.append(f"Bối cảnh: {self.setting}")
        if self.visual_cues: parts.append("Chi tiết phụ: " + ", ".join(self.visual_cues))
        return " | ".join(parts).strip()


# =============================================================================
# Base Interface
# =============================================================================

class BaseVisionProvider:
    def caption_keyframe(self, image: Union[Path, Image.Image]) -> str:
        raise NotImplementedError

    def extract_scene_signals(self, image: Union[Path, Image.Image]) -> Dict[str, Any]:
        raise NotImplementedError

    def unload(self) -> None:
        raise NotImplementedError


# =============================================================================
# Ollama Qwen-VL Provider
# =============================================================================

class OllamaQwenVisionProvider(BaseVisionProvider):
    def __init__(self, model_name: Optional[str] = None, base_url: Optional[str] = None):
        self.model_name = model_name or VISION_CONFIG.model_name
        self.base_url = base_url or VISION_CONFIG.base_url
        self._validate_server()

    def _validate_server(self) -> None:
        try:
            if not _check_ollama_server(self.base_url):
                raise RuntimeError(f"Ollama server not available at {self.base_url}")

            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]

            if self.model_name not in models:
                logger.warning(f"Vision model '{self.model_name}' chưa được nạp trong Ollama.")

            log_model_loading(self.model_name, "loaded")
            logger.info(f"✅ Đôi mắt hệ thống đã sẵn sàng: {self.model_name}")

        except Exception as e:
            log_exception(e, "OllamaQwenVisionProvider._validate_server")
            raise

    def caption_keyframe(self, image: Union[Path, Image.Image]) -> str:
        signals = self.extract_scene_signals(image)
        return self._signals_to_caption(signals)

    def extract_scene_signals(self, image: Union[Path, Image.Image]) -> Dict[str, Any]:
        """Hàm trích xuất tín hiệu thị giác, chạy trực tiếp trên RAM để tối ưu I/O."""
        pil_img = None
        try:
            if isinstance(image, Path):
                pil_img = Image.open(image).convert("RGB")
            else:
                pil_img = image.convert("RGB") if image.mode != "RGB" else image
        except Exception as e:
            log_exception(e, "Vision mở ảnh thất bại")
            return self._fallback_signals()

        try:
            raw = self._analyze_image(pil_img)
            parsed = self._parse_model_output(raw)
            if parsed is None:
                return self._fallback_signals()

            signals = self._normalize_signals(parsed)
            return signals.to_dict()

        except Exception as e:
            log_exception(e, "OllamaQwenVisionProvider.extract_scene_signals")
            return self._fallback_signals()
        finally:
            _free_memory()

    def _analyze_image(self, image: Image.Image) -> str:
        image = _resize_image(image, VISION_CONFIG.max_image_size)
        image_b64 = _image_to_base64(image, VISION_CONFIG.jpeg_quality)
        
        prompt = (
            "Bạn là AI bóc tách tín hiệu thị giác khung hình video cho editor dựng phim tại Việt Nam.\n"
            "Nhiệm vụ: Phân tích ảnh và trả về JSON chứa thông tin kỹ thuật thô theo đúng mẫu sau:\n"
            "{\n"
            '  "shot_type": "cận cảnh | trung cảnh | toàn cảnh | góc quay từ trên xuống | không rõ",\n'
            '  "main_subjects": ["chủ thể chính 1", "chủ thể chính 2"],\n'
            '  "actions": ["hành động 1", "hành động 2"],\n'
            '  "setting": "bối cảnh không gian ngắn",\n'
            '  "visual_cues": ["chi tiết ánh sáng hoặc đạo cụ nổi bật"]\n'
            "}\n"
            "Quy tắc:\n"
            "- Trả về văn bản TIẾNG VIỆT ngắn gọn, thực tế, nhìn thấy rõ.\n"
            "- Tuyệt đối không dùng tiêu đề tiếng Anh, không giải thích."
        )

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": VISION_CONFIG.temperature,
                "num_predict": VISION_CONFIG.num_predict,
                "num_ctx": VISION_CONFIG.num_ctx,
                "num_thread": VISION_CONFIG.num_thread,
            },
            "keep_alive": -1,
        }

        last_error = None
        for attempt in range(VISION_CONFIG.max_retries + 1):
            try:
                resp = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=VISION_CONFIG.request_timeout_sec,
                )
                resp.raise_for_status()
                output = (resp.json().get("response") or "").strip()
                if output:
                    return output
                last_error = RuntimeError("Empty response từ Vision Model")
            except Exception as e:
                last_error = e
                if attempt < VISION_CONFIG.max_retries:
                    time.sleep(VISION_CONFIG.retry_delay_sec * (attempt + 1))

        raise RuntimeError(f"Vision model failed: {last_error}")

    def _parse_model_output(self, raw_text: str) -> Optional[Dict[str, Any]]:
        repaired = _repair_json(raw_text)
        if not repaired: return None
        try:
            parsed = json.loads(repaired)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None

    def _normalize_signals(self, parsed: Dict[str, Any]) -> VisionSceneSignals:
        shot_type = _clean_line(str(parsed.get("shot_type", "") or ""))
        setting = _clean_line(str(parsed.get("setting", "") or ""))

        subjects = _safe_list(parsed.get("main_subjects"))
        actions = _safe_list(parsed.get("actions"))
        cues = _safe_list(parsed.get("visual_cues"))

        trash = {"main subjects", "scene type", "visible objects", "actions", "setting", "visual cues", "n/a", "none", "không rõ"}

        def clean_items(items: List[str], limit: int) -> List[str]:
            cleaned = []
            for item in items:
                x = _clean_line(item)
                if x and x.lower() not in trash:
                    cleaned.append(x)
            return _dedupe_keep_order(cleaned, limit=limit)

        subjects = clean_items(subjects, limit=4)
        actions = clean_items(actions, limit=3)
        cues = clean_items(cues, limit=5)

        if shot_type.lower() in trash: shot_type = "không rõ"
        if setting.lower() in trash: setting = "khung hình video"

        signals = VisionSceneSignals(
            shot_type=shot_type[:80],
            main_subjects=subjects,
            actions=actions,
            setting=setting[:160],
            visual_cues=cues,
        )
        signals.raw_caption = signals.to_search_hint_text()
        return signals

    def _signals_to_caption(self, signals: Dict[str, Any]) -> str:
        shot = (signals.get("shot_type") or "").strip()
        subjects = signals.get("main_subjects") or []
        actions = signals.get("actions") or []
        setting = (signals.get("setting") or "").strip()
        cues = signals.get("visual_cues") or []

        parts = []
        if shot and shot != "không rõ": parts.append(f"Cỡ cảnh: {shot}")
        if subjects: parts.append("Chủ thể: " + ", ".join(subjects))
        if actions: parts.append("Hành động: " + ", ".join(actions))
        if setting and setting != "khung hình video": parts.append(f"Bối cảnh: {setting}")
        if cues: parts.append("Chi tiết: " + ", ".join(cues))

        text = " | ".join(parts).strip()
        return text or "Khung hình video, chưa xác định rõ thông số thị giác."

    def _fallback_signals(self) -> Dict[str, Any]:
        signals = VisionSceneSignals(shot_type="không rõ", main_subjects=[], actions=[], setting="khung hình video", visual_cues=[])
        signals.raw_caption = "Khung hình video"
        return signals.to_dict()


# =============================================================================
# Legacy-compatible wrapper class
# =============================================================================

class QwenVLModel:
    """Wrapper duy trì khả năng tương thích ngược với luồng code cũ."""
    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        self.provider = OllamaQwenVisionProvider(model_name=model_name)

    def analyze_image(self, image: Image.Image, prompt: str = None, max_new_tokens: int = None, temperature: float = 0.2) -> str:
        try:
            return self.provider.caption_keyframe(image)
        except Exception as e:
            log_exception(e, "QwenVLModel.analyze_image")
            return ""

    def batch_analyze_images(self, images: List[Image.Image], prompts: List[str] = None, batch_size: int = 1) -> List[str]:
        return [self.analyze_image(img) for img in images]


# =============================================================================
# Manager
# =============================================================================

class ModelManager:
    """Quản lý tập trung vòng đời nạp mô hình Vision."""
    def __init__(self):
        self.qwen_vl: Optional[OllamaQwenVisionProvider] = None
        self.loaded_models: set = set()

    def load_qwen_vl(self):
        if self.qwen_vl is None:
            self.qwen_vl = OllamaQwenVisionProvider()
            self.loaded_models.add("qwen_vl")

    def load_models_for_mode(self, mode: str):
        mode_config = config.get_processing_mode_config(mode)
        # Chỉ tập trung tải duy nhất Qwen-VL làm mắt phân tích dữ liệu video
        if mode_config.get("use_qwen_vl", True):
            self.load_qwen_vl()
        logger.info(f"Vision models loaded for mode='{mode}': {sorted(self.loaded_models)}")

    def unload_all(self):
        self.qwen_vl = None
        self.loaded_models.clear()
        _free_memory()
        logger.info("Vision models đã giải phóng hoàn toàn khỏi bộ nhớ RAM")


# =============================================================================
# Factory
# =============================================================================

def create_vision_provider() -> BaseVisionProvider:
    return OllamaQwenVisionProvider()