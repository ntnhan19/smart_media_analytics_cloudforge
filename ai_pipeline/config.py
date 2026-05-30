"""
Video AI Editor Configuration
Tối ưu cho GTX 1650 4GB VRAM — 4-bit quantization, model nhẹ
"""

import os
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass, field

# ── Base directories ──────────────────────────────────────────────────────────
BASE_DIR       = Path(__file__).parent.absolute()
VIDEOS_DIR     = BASE_DIR / "videos"
PROXIES_DIR    = BASE_DIR / "proxies"
THUMBNAILS_DIR = BASE_DIR / "thumbnails"
KEYFRAMES_DIR  = BASE_DIR / "keyframes"
OUTPUT_DIR     = BASE_DIR / "output"
LOGS_DIR       = BASE_DIR / "logs"
DB_DIR         = BASE_DIR / "database"

for _d in [VIDEOS_DIR, PROXIES_DIR, THUMBNAILS_DIR,
           KEYFRAMES_DIR, OUTPUT_DIR, LOGS_DIR, DB_DIR]:
    _d.mkdir(parents=True, exist_ok=True)


@dataclass
class ModelConfig:
    """
    Cấu hình model — tối ưu cho GTX 1650 4GB.

    Thay đổi so với bản gốc:
      - qwen_vl_model   : 7B  → 2B  (giảm ~5GB VRAM)
      - florence_model  : large → base (giảm ~300MB VRAM)
      - refinement_llm  : Llama-8B → Qwen-1.5B (giảm ~3GB VRAM)
      - whisper_model   : large-v3 → base (giảm ~1GB VRAM)
      - dtype           : bfloat16 → float16 (GTX 1650 không hỗ trợ bfloat16)
      - load_in_4bit    : True (BitsAndBytes NF4 — cắt VRAM thêm ~75%)
      - use_flash_attention : False (GTX 1650 / Turing không hỗ trợ)
    """

    # ── Vision ─────────────────────────────────────────────────────────────────
    # 2B thay 7B: fit vào 4GB VRAM sau quantization 4-bit (~1.2GB)
    qwen_vl_model: str = "Qwen/Qwen2.5-VL-2B-Instruct"

    # base thay large: ~270MB thay ~900MB, độ chính xác vẫn ổn cho object detection
    florence_model: str = "microsoft/Florence-2-base"

    # Không dùng InternVideo2 — quá nặng cho 4GB
    internvideo_model: str = ""   # disabled

    # ── Refinement LLM ─────────────────────────────────────────────────────────
    # 1.5B thay Llama-8B: ~0.8GB sau 4-bit, đủ để merge JSON output
    refinement_llm:     str = "Qwen/Qwen2-1.5B-Instruct"
    refinement_llm_alt: str = "Qwen/Qwen2-1.5B-Instruct"   # fallback giống nhau

    # ── Embedding & Reranker (chạy trên CPU — không tốn VRAM) ────────────────
    embedding_model: str = "BAAI/bge-m3"
    reranker_model:  str = "BAAI/bge-reranker-v2-m3"

    # ── ASR ────────────────────────────────────────────────────────────────────
    # base: ~74MB, đủ nhanh, RAM thay vì VRAM
    whisper_model: str = "base"

    # ── Device / precision ─────────────────────────────────────────────────────
    device: str = "cuda"

    # float16 vì GTX 1650 (Turing) không hỗ trợ bfloat16
    dtype: str = "float16"

    # ── Quantization ───────────────────────────────────────────────────────────
    load_in_8bit: bool = False  # không dùng 8-bit, dùng 4-bit tốt hơn
    load_in_4bit: bool = True   # BitsAndBytes NF4 — cắt VRAM ~75%

    # Flash Attention 2 yêu cầu Ampere (RTX 30xx+), GTX 1650 không hỗ trợ
    use_flash_attention: bool = False

    # ── Image resize trước inference (tránh OOM) ──────────────────────────────
    # Qwen2.5-VL-2B có thể nhận ảnh lớn nhưng sẽ OOM trên 4GB
    max_image_size: int = 448   # pixel, resize về 448×448 trước khi đưa vào model

    # ── Generation limits (tránh OOM khi decode) ─────────────────────────────
    max_new_tokens_vision:     int = 256   # đủ cho scene description
    max_new_tokens_refinement: int = 512   # đủ cho JSON merge


@dataclass
class VideoProcessingConfig:
    """Cấu hình xử lý video"""

    # Proxy nhỏ hơn → ít RAM hơn khi load frame
    proxy_height: int = 480   # 720 → 480, đủ để analyze
    proxy_crf:    int = 28    # chất lượng thấp hơn = file nhỏ hơn
    proxy_preset: str = "fast"

    keyframe_interval: int = 30
    keyframe_quality:  int = 3

    scene_threshold:   float = 10.0
    min_scene_length:  float = 1.0

    # Giảm frames/scene để tránh OOM khi batch inference
    frames_per_scene_fast:  int = 1   # 3 → 1: 1 frame/scene trong fast mode
    frames_per_scene_high:  int = 2   # 5 → 2
    frames_per_scene_ultra: int = 3   # 8 → 3 (ultra bị disable nhưng để đây)

    max_video_duration: int = 3600
    max_video_size:     int = 10 * 1024 * 1024 * 1024


@dataclass
class AnalysisConfig:
    """
    Cấu hình phân tích — ultra mode bị disable cho GTX 1650.

    Thay đổi batch_size:
      fast: 4 → 1  (sequential inference, tránh OOM)
      high: 2 → 1
    """

    processing_modes: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "fast": {
            "use_qwen_vl":    True,
            "use_florence":   False,   # tiết kiệm VRAM tối đa
            "use_internvideo":False,
            "frames_per_scene": 1,
            "use_refinement": False,
            "batch_size":     1,       # sequential — tránh OOM
        },
        "high": {
            "use_qwen_vl":    True,
            "use_florence":   True,    # Florence-base fit ~500MB
            "use_internvideo":False,
            "frames_per_scene": 2,
            "use_refinement": True,    # Qwen-1.5B ~800MB sau 4-bit
            "batch_size":     1,
        },
        # ultra bị disable — thay bằng alias của high
        "ultra": {
            "use_qwen_vl":    True,
            "use_florence":   True,
            "use_internvideo":False,   # disabled cho 4GB VRAM
            "frames_per_scene": 2,
            "use_refinement": True,
            "batch_size":     1,
        },
    })

    min_confidence:      float = 0.3
    high_confidence:     float = 0.7
    max_tags_per_frame:  int   = 20   # 30 → 20
    max_objects_per_frame: int = 30   # 50 → 30
    temporal_window:     float = 5.0
    motion_threshold:    float = 0.1


@dataclass
class SearchConfig:
    """Cấu hình tìm kiếm"""

    embedding_dimension: int   = 1024
    top_k_initial:       int   = 30    # 50 → 30, tiết kiệm RAM
    top_k_final:         int   = 10    # 20 → 10

    vector_weight: float = 0.6
    bm25_weight:   float = 0.4

    use_reranker:   bool = True
    reranker_top_k: int  = 5     # 10 → 5

    min_score:   float = 0.1
    max_results: int   = 50      # 100 → 50


@dataclass
class DatabaseConfig:
    """Cấu hình database"""

    chroma_persist_dir:    Path = DB_DIR / "chroma"
    sqlite_db_path:        Path = DB_DIR / "metadata.db"
    chroma_collection_name: str = "video_frames"
    enable_wal:            bool = True
    cache_size:            int  = 5000   # 10000 → 5000


@dataclass
class WebConfig:
    """Cấu hình web interface"""

    host:  str  = "0.0.0.0"
    port:  int  = 8000
    debug: bool = True
    reload: bool = True

    max_upload_size: int = 10 * 1024 * 1024 * 1024
    allowed_extensions: set = field(default_factory=lambda: {
        ".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"
    })
    secret_key:      str = "change-this-in-production"
    session_timeout: int = 3600


@dataclass
class LoggingConfig:
    """Cấu hình logging"""

    log_level:   str  = "INFO"
    log_format:  str  = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file:    Path = LOGS_DIR / "app.log"
    max_bytes:   int  = 10 * 1024 * 1024
    backup_count: int = 5


class Config:
    """Main configuration class"""

    def __init__(self):
        self.model    = ModelConfig()
        self.video    = VideoProcessingConfig()
        self.analysis = AnalysisConfig()
        self.search   = SearchConfig()
        self.database = DatabaseConfig()
        self.web      = WebConfig()
        self.logging  = LoggingConfig()

    def get_processing_mode_config(self, mode: str) -> Dict[str, Any]:
        if mode not in self.analysis.processing_modes:
            raise ValueError(f"Invalid processing mode: {mode}")
        return self.analysis.processing_modes[mode]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model":    self.model.__dict__,
            "video":    self.video.__dict__,
            "analysis": self.analysis.__dict__,
            "search":   self.search.__dict__,
            "database": self.database.__dict__,
            "web":      self.web.__dict__,
            "logging":  self.logging.__dict__,
        }


# ── Global instance ───────────────────────────────────────────────────────────
config = Config()


def load_env_config():
    """Load overrides từ environment variables"""
    if os.getenv("VIDEO_AI_DEBUG"):
        config.web.debug = True
        config.logging.log_level = "DEBUG"
    if os.getenv("VIDEO_AI_PORT"):
        config.web.port = int(os.getenv("VIDEO_AI_PORT"))
    if os.getenv("VIDEO_AI_DEVICE"):
        config.model.device = os.getenv("VIDEO_AI_DEVICE")
    if os.getenv("VIDEO_AI_MODEL_DTYPE"):
        config.model.dtype = os.getenv("VIDEO_AI_MODEL_DTYPE")


load_env_config()
