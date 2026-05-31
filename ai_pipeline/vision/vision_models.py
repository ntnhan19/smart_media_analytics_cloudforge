"""
Vision Models — tối ưu GTX 1650 4GB
- Qwen2.5-VL-2B-Instruct với 4-bit quantization
- Florence-2-base với float16
- Sequential inference (batch_size=1), image resize 448px
- torch.inference_mode() thay torch.no_grad() (nhanh hơn, ít VRAM hơn)
- gc.collect() + torch.cuda.empty_cache() sau mỗi inference
"""

import gc
import torch
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from PIL import Image
import numpy as np
from transformers import (
    AutoProcessor,
    AutoModelForCausalLM,
    Qwen2VLForConditionalGeneration,
    BitsAndBytesConfig,
)

from ai_pipeline.config import config
from utils.logger import logger, log_model_loading, log_exception


# ── Shared 4-bit quantization config ─────────────────────────────────────────
def _make_bnb_config() -> BitsAndBytesConfig:
    """
    NF4 quantization:
    - load_in_4bit        : kích hoạt 4-bit loading
    - bnb_4bit_quant_type : NF4 (Normal Float 4) — chất lượng tốt nhất cho 4-bit
    - bnb_4bit_use_double_quant : quantize thêm các scale factors (~0.4 bit tiết kiệm thêm)
    - bnb_4bit_compute_dtype    : float16 để compute nhanh trên GPU
    """
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )


def _free_vram():
    """Giải phóng VRAM sau mỗi inference — quan trọng trên 4GB."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def _resize_image(image: Image.Image, max_size: int = None) -> Image.Image:
    """
    Resize ảnh về max_size×max_size trước khi đưa vào model.
    Lý do: ảnh lớn (1080p+) tiêu tốn rất nhiều VRAM khi tokenize thành visual tokens.
    448px là điểm cân bằng tốt giữa chất lượng và VRAM cho 2B model.
    """
    max_size = max_size or config.model.max_image_size
    w, h = image.size
    if max(w, h) <= max_size:
        return image
    scale  = max_size / max(w, h)
    new_w  = int(w * scale)
    new_h  = int(h * scale)
    return image.resize((new_w, new_h), Image.LANCZOS)


# ── Qwen2.5-VL-2B ─────────────────────────────────────────────────────────────

class QwenVLModel:
    """
    Qwen2.5-VL-2B-Instruct với 4-bit quantization.

    VRAM estimate sau load:
      - 2B params × 0.5 bytes (4-bit) ≈ ~1.0-1.2 GB VRAM
      - Activation memory khi inference 448px ảnh ≈ ~0.5-0.8 GB
      - Tổng: ~1.5-2.0 GB → an toàn trên 4GB GTX 1650
    """

    def __init__(self, model_name: str = None, device: str = None):
        self.model_name = model_name or config.model.qwen_vl_model
        self.device     = device     or config.model.device
        self.model      = None
        self.processor  = None
        self._load_model()

    def _load_model(self):
        try:
            log_model_loading(self.model_name, "loading")

            self.processor = AutoProcessor.from_pretrained(
                self.model_name,
                trust_remote_code=True,
            )

            # 4-bit quantization — không dùng flash_attention (GTX 1650 không hỗ trợ)
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_name,
                quantization_config=_make_bnb_config(),
                device_map="auto",         # tự phân bổ layers giữa GPU/CPU nếu cần
                trust_remote_code=True,
                # KHÔNG set attn_implementation="flash_attention_2"
            )

            self.model.eval()
            log_model_loading(self.model_name, "loaded")
            logger.info(
                f"Qwen-VL loaded | "
                f"VRAM: {torch.cuda.memory_allocated()/1e9:.2f} GB"
            )

        except Exception as e:
            log_model_loading(self.model_name, "failed")
            log_exception(e, "QwenVLModel._load_model")
            raise

    def analyze_image(
        self,
        image: Image.Image,
        prompt: str = None,
        max_new_tokens: int = None,
        temperature: float = 0.3,    # thấp hơn → ổn định hơn, ít token padding
    ) -> str:
        try:
            # Resize trước — quan trọng để tránh OOM
            image = _resize_image(image)

            if prompt is None:
                prompt = self._get_default_prompt()

            max_new_tokens = max_new_tokens or config.model.max_new_tokens_vision

            messages = [{
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text",  "text":  prompt},
                ],
            }]

            text   = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = self.processor(
                text=[text],
                images=[image],
                return_tensors="pt",
                padding=True,
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # torch.inference_mode() nhanh hơn no_grad, không lưu grad buffer
            with torch.inference_mode():
                output_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    do_sample=False,       # greedy decode — ổn định hơn, nhanh hơn
                    repetition_penalty=1.1,
                    pad_token_id=self.processor.tokenizer.pad_token_id,
                )

            generated_text = self.processor.batch_decode(
                output_ids[:, inputs["input_ids"].shape[1]:],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0]

            return generated_text.strip()

        except torch.cuda.OutOfMemoryError:
            logger.error("OOM trong analyze_image — giải phóng VRAM và thử lại với ảnh nhỏ hơn")
            _free_vram()
            # Retry với ảnh nhỏ hơn
            try:
                small_image = _resize_image(image, max_size=224)
                return self.analyze_image(small_image, prompt, max_new_tokens=128)
            except Exception:
                return ""

        except Exception as e:
            log_exception(e, "QwenVLModel.analyze_image")
            return ""

        finally:
            # Luôn giải phóng sau inference
            _free_vram()

    def _get_default_prompt(self) -> str:
        """
        Prompt ngắn gọn — ít token → ít VRAM, đủ để tạo metadata tốt.
        Tối ưu cho landscape, drone, travel, fashion/model shots.
        """
        return (
            "Describe this video frame concisely covering: "
            "1) Scene type and setting (landscape/mountain/forest/beach/urban/indoor) "
            "2) People if any (appearance, clothing, action, emotion) "
            "3) Lighting and time of day (golden hour/day/night/foggy) "
            "4) Camera angle (aerial/drone/eye-level/low angle) "
            "5) Mood and colors "
            "6) Key objects visible. "
            "Be specific. Max 150 words."
        )

    def batch_analyze_images(
        self,
        images: List[Image.Image],
        prompts: List[str] = None,
        batch_size: int = 1,   # luôn 1 trên 4GB VRAM
    ) -> List[str]:
        """
        Sequential inference (batch_size=1).
        Không batch nhiều ảnh cùng lúc vì VRAM không đủ.
        """
        results = []
        if prompts is None:
            prompts = [self._get_default_prompt()] * len(images)

        for img, prompt in zip(images, prompts):
            result = self.analyze_image(img, prompt)
            results.append(result)
            _free_vram()   # giải phóng sau mỗi frame

        return results


# ── Florence-2-base ────────────────────────────────────────────────────────────

class Florence2Model:
    """
    Florence-2-base với float16.
    Không dùng 4-bit vì Florence là encoder-decoder nhỏ (~250MB),
    4-bit sẽ làm giảm chất lượng object detection đáng kể.

    VRAM estimate: ~500MB — an toàn cùng lúc với Qwen-VL đã unload.
    """

    def __init__(self, model_name: str = None, device: str = None):
        self.model_name = model_name or config.model.florence_model
        self.device     = device     or config.model.device
        self.model      = None
        self.processor  = None
        self._load_model()

    def _load_model(self):
        try:
            log_model_loading(self.model_name, "loading")

            self.processor = AutoProcessor.from_pretrained(
                self.model_name,
                trust_remote_code=True,
            )

            # float16 — không cần 4-bit vì model đã nhỏ
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,
                trust_remote_code=True,
            ).to(self.device)

            self.model.eval()
            log_model_loading(self.model_name, "loaded")

        except Exception as e:
            log_model_loading(self.model_name, "failed")
            log_exception(e, "Florence2Model._load_model")
            raise

    def _run_task(
        self,
        task_prompt: str,
        image: Image.Image,
        max_new_tokens: int = 512,   # 1024 → 512 tiết kiệm VRAM
    ) -> Tuple[str, Dict[str, Any]]:
        """Shared inference logic cho tất cả Florence tasks."""
        image = _resize_image(image)

        inputs = self.processor(
            text=task_prompt,
            images=image,
            return_tensors="pt",
        ).to(self.device)

        with torch.inference_mode():
            generated_ids = self.model.generate(
                input_ids=inputs["input_ids"],
                pixel_values=inputs["pixel_values"],
                max_new_tokens=max_new_tokens,
                num_beams=1,         # greedy — 3 beams quá tốn VRAM
                do_sample=False,
            )

        generated_text = self.processor.batch_decode(
            generated_ids, skip_special_tokens=False
        )[0]

        parsed = self.processor.post_process_generation(
            generated_text,
            task=task_prompt,
            image_size=(image.width, image.height),
        )

        return generated_text, parsed

    def detect_objects(self, image: Image.Image) -> Dict[str, Any]:
        try:
            _, parsed = self._run_task("<OD>", image)
            return parsed
        except Exception as e:
            log_exception(e, "Florence2Model.detect_objects")
            return {}
        finally:
            _free_vram()

    def dense_caption(self, image: Image.Image) -> Dict[str, Any]:
        try:
            _, parsed = self._run_task("<DENSE_REGION_CAPTION>", image)
            return parsed
        except Exception as e:
            log_exception(e, "Florence2Model.dense_caption")
            return {}
        finally:
            _free_vram()

    def caption_to_phrase_grounding(
        self, image: Image.Image, caption: str
    ) -> Dict[str, Any]:
        try:
            _, parsed = self._run_task("<CAPTION_TO_PHRASE_GROUNDING>", image)
            return parsed
        except Exception as e:
            log_exception(e, "Florence2Model.caption_to_phrase_grounding")
            return {}
        finally:
            _free_vram()


# ── ModelManager ───────────────────────────────────────────────────────────────

class ModelManager:
    """
    Quản lý vision models — load tuần tự, không giữ cả 2 model trong VRAM cùng lúc.

    Chiến lược GTX 1650:
      - Chỉ load 1 model tại một thời điểm khi có thể
      - Unload trước khi load model tiếp theo trong high/ultra mode
    """

    def __init__(self):
        self.qwen_vl:    Optional[QwenVLModel]    = None
        self.florence:   Optional[Florence2Model] = None
        self.loaded_models: set = set()

    def load_qwen_vl(self):
        if self.qwen_vl is None:
            self.qwen_vl = QwenVLModel()
            self.loaded_models.add("qwen_vl")

    def load_florence(self):
        if self.florence is None:
            self.florence = Florence2Model()
            self.loaded_models.add("florence")

    def load_models_for_mode(self, mode: str):
        mode_config = config.get_processing_mode_config(mode)

        if mode_config["use_qwen_vl"]:
            self.load_qwen_vl()

        if mode_config["use_florence"]:
            self.load_florence()

        vram_used = torch.cuda.memory_allocated() / 1e9 if torch.cuda.is_available() else 0
        logger.info(
            f"Models loaded for '{mode}': {self.loaded_models} | "
            f"VRAM: {vram_used:.2f} GB"
        )

    def unload_qwen_vl(self):
        """
        Unload Qwen để nhường VRAM cho model khác.
        FIX: phải xóa model khỏi GPU (cpu() + del) trước khi gán None,
        nếu không PyTorch giữ tham chiếu và VRAM không thực sự được giải phóng.
        """
        if self.qwen_vl is not None:
            qwen_vl = self.qwen_vl
            self.qwen_vl = None
            try:
                if hasattr(qwen_vl, "model") and qwen_vl.model is not None:
                    try:
                        qwen_vl.model.cpu()
                    except Exception:
                        pass
                    del qwen_vl.model
                if hasattr(qwen_vl, "processor") and qwen_vl.processor is not None:
                    del qwen_vl.processor
            except Exception as e:
                logger.warning(f"Lỗi khi unload Qwen-VL: {e}")
            finally:
                self.loaded_models.discard("qwen_vl")
                _free_vram()
                if torch.cuda.is_available() and hasattr(torch.cuda, "ipc_collect"):
                    torch.cuda.ipc_collect()
                time.sleep(1)
                _free_vram()
                vram = torch.cuda.memory_allocated() / 1e9 if torch.cuda.is_available() else 0
                logger.info(f"Qwen-VL unloaded | VRAM còn lại: {vram:.2f} GB")
                del qwen_vl

    def unload_florence(self):
        """Unload Florence-2 và giải phóng VRAM."""
        if self.florence is not None:
            try:
                if hasattr(self.florence, "model") and self.florence.model is not None:
                    self.florence.model.cpu()
                    del self.florence.model
                if hasattr(self.florence, "processor") and self.florence.processor is not None:
                    del self.florence.processor
            except Exception as e:
                logger.warning(f"Lỗi khi unload Florence: {e}")
            finally:
                self.florence = None
                self.loaded_models.discard("florence")
                _free_vram()
                logger.info("Florence-2 unloaded")

    def unload_all(self):
        """
        Unload toàn bộ models và đảm bảo VRAM sạch hoàn toàn.
        Gọi sau mỗi video để tránh VRAM fragmentation giữa các video.
        """
        self.unload_qwen_vl()
        self.unload_florence()
        self.loaded_models.clear()
        _free_vram()
        _free_vram()  # gọi 2 lần để PyTorch allocator thực sự release
        time.sleep(2)  # chờ PyTorch allocator settle, giúp VRAM sạch thực sự
        vram = torch.cuda.memory_allocated() / 1e9 if torch.cuda.is_available() else 0
        reserved = torch.cuda.memory_reserved() / 1e9 if torch.cuda.is_available() else 0
        logger.info(f"All models unloaded | allocated: {vram:.2f} GB | reserved: {reserved:.2f} GB")