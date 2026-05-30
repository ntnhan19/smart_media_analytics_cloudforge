"""
LLM Refinement — tối ưu GTX 1650 4GB
- Qwen2-1.5B-Instruct với 4-bit quantization (~0.8GB VRAM)
- max_new_tokens giảm xuống 512 (đủ cho JSON merge)
- torch.inference_mode() + gc.collect() sau mỗi call
- JSON output ngắn gọn hơn để tránh generation timeout
"""

import gc
import json
import re
import torch
from typing import Dict, List, Any, Optional
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)

from config import config
from utils.logger import logger, log_model_loading, log_exception


def _make_bnb_config() -> BitsAndBytesConfig:
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )


def _free_vram():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


class RefinementLLM:
    """
    Qwen2-1.5B-Instruct để merge và structure JSON output từ vision models.

    VRAM estimate sau 4-bit load: ~0.8 GB
    Dùng sau khi unload Qwen-VL để đảm bảo không OOM.
    """

    def __init__(self, model_name: str = None, device: str = None):
        self.model_name = model_name or config.model.refinement_llm
        self.device     = device     or config.model.device
        self.model      = None
        self.tokenizer  = None
        self._load_model()

    def _load_model(self):
        try:
            log_model_loading(self.model_name, "loading")

            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
            )

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=_make_bnb_config(),
                device_map="auto",
                trust_remote_code=True,
            )

            self.model.eval()
            log_model_loading(self.model_name, "loaded")
            logger.info(
                f"RefinementLLM loaded | "
                f"VRAM: {torch.cuda.memory_allocated()/1e9:.2f} GB"
            )

        except Exception as e:
            log_model_loading(self.model_name, "failed")
            log_exception(e, "RefinementLLM._load_model")
            raise

    def refine_analysis(
        self,
        vision_outputs: Dict[str, str],
        timestamp: float,
        scene_id: int,
        max_new_tokens: int = None,
        temperature: float = 0.1,    # rất thấp → JSON ổn định, không hallucinate
    ) -> Dict[str, Any]:
        try:
            max_new_tokens = max_new_tokens or config.model.max_new_tokens_refinement

            prompt = self._build_refinement_prompt(vision_outputs, timestamp, scene_id)

            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user",   "content": prompt},
            ]

            formatted = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )

            inputs = self.tokenizer(
                formatted,
                return_tensors="pt",
                truncation=True,
                max_length=1536,   # giới hạn input để tránh OOM
            ).to(self.device)

            with torch.inference_mode():
                output_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,           # greedy — JSON nhất quán hơn
                    repetition_penalty=1.05,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )

            generated_text = self.tokenizer.decode(
                output_ids[0][inputs["input_ids"].shape[1]:],
                skip_special_tokens=True,
            )

            return self._parse_json_output(generated_text)

        except torch.cuda.OutOfMemoryError:
            logger.error("OOM trong refine_analysis — dùng fallback")
            _free_vram()
            return self._get_fallback_output(vision_outputs, timestamp, scene_id)

        except Exception as e:
            log_exception(e, "RefinementLLM.refine_analysis")
            return self._get_fallback_output(vision_outputs, timestamp, scene_id)

        finally:
            _free_vram()

    def _get_system_prompt(self) -> str:
        # Ngắn gọn hơn → ít token hơn → ít VRAM
        return (
            "You are a video metadata AI. "
            "Merge vision model outputs into compact JSON. "
            "Output ONLY valid JSON, no markdown, no explanation."
        )

    def _build_refinement_prompt(
        self,
        vision_outputs: Dict[str, str],
        timestamp: float,
        scene_id: int,
    ) -> str:
        """
        Prompt ngắn hơn bản gốc — tránh input quá dài gây OOM khi tokenize.
        Giới hạn qwen_vl output ở 800 chars thay vì 3000.
        """
        qwen_text = str(vision_outputs.get("qwen_vl", ""))[:800]

        florence_obj = vision_outputs.get("florence_objects", {})
        if isinstance(florence_obj, dict):
            # Chỉ lấy labels, bỏ bounding boxes để tiết kiệm tokens
            labels = florence_obj.get("<OD>", {}).get("labels", [])
            florence_text = ", ".join(labels[:20]) if labels else str(florence_obj)[:200]
        else:
            florence_text = str(florence_obj)[:200]

        return (
            f"Timestamp: {timestamp:.1f}s | Scene: {scene_id}\n\n"
            f"QWEN-VL:\n{qwen_text}\n\n"
            f"DETECTED OBJECTS: {florence_text}\n\n"
            "Create this JSON:\n"
            "{"
            '"summary":"2 sentences",'
            '"scene":{"type":"","setting":"","atmosphere":""},'
            '"people":[{"clothing":"","action":"","emotion":""}],'
            '"landscape":{"features":[],"weather":"","time_of_day":"","lighting":""},'
            '"camera":{"shot_type":"","angle":"","movement":""},'
            '"colors":{"dominant":[],"mood":""},'
            '"tags":{"scene_tags":[],"mood_tags":[],"object_tags":[]},'
            '"searchable_text":"dense search text here",'
            '"confidence_score":0.0'
            "}"
        )

    def _parse_json_output(self, text: str) -> Dict[str, Any]:
        try:
            text = text.strip()
            # Bỏ markdown fences
            for fence in ("```json", "```"):
                if text.startswith(fence):
                    text = text[len(fence):]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            return json.loads(text)

        except json.JSONDecodeError:
            # Thử extract JSON bằng regex
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except Exception:
                    pass
            return self._get_empty_structure()

    def _get_empty_structure(self) -> Dict[str, Any]:
        return {
            "summary": "",
            "scene":     {"type": "unknown", "setting": "", "atmosphere": ""},
            "people":    [],
            "landscape": {"features": [], "weather": "", "time_of_day": "", "lighting": ""},
            "camera":    {"shot_type": "", "angle": "", "movement": ""},
            "colors":    {"dominant": [], "mood": ""},
            "tags":      {"scene_tags": [], "mood_tags": [], "object_tags": []},
            "searchable_text": "",
            "confidence_score": 0.0,
        }

    def _get_fallback_output(
        self,
        vision_outputs: Dict[str, str],
        timestamp: float,
        scene_id: int,
    ) -> Dict[str, Any]:
        result = self._get_empty_structure()
        qwen_text = vision_outputs.get("qwen_vl", "")
        result["summary"]          = qwen_text[:300]
        result["searchable_text"]  = qwen_text[:500]
        result["confidence_score"] = 0.3
        return result


def create_refinement_llm() -> RefinementLLM:
    return RefinementLLM()
