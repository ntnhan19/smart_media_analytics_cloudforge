"""
Video AI Editor Configuration — Thuần Ollama + Tối ưu tốc độ
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

for _d in [VIDEOS_DIR, PROXIES_DIR, THUMBNAILS_DIR, KEYFRAMES_DIR, OUTPUT_DIR, LOGS_DIR, DB_DIR]:
    _d.mkdir(parents=True, exist_ok=True)


@dataclass
class ModelConfig:
    """Cấu hình Model — Thuần Ollama"""

    # Vision
    qwen_vl_model: str = "qwen2.5vl:3b"

    # Refinement LLM (Ollama)
    refinement_llm: str = "qwen2:1.5b"

    # Embedding
    embedding_model: str = "bge-m3:latest"
    reranker_model:  str = "bge-reranker-v2-m3"

    # ASR
    asr_provider: str = os.getenv("AI_PROVIDER", "aws")
    whisper_model: str = "base"

    # Image & Generation
    max_image_size: int = 448
    max_new_tokens_vision:     int = 200
    max_new_tokens_refinement: int = 512

    device: str = "cuda"
    dtype: str = "float16"
    load_in_4bit: bool = True
    use_flash_attention: bool = False


@dataclass
class VideoProcessingConfig:
    """Cấu hình xử lý video - Tối ưu tốc độ"""

    proxy_height: int = 480
    proxy_crf:    int = 28
    proxy_preset: str = "fast"

    scene_threshold:   float = 27.0
    min_scene_length:  float = 2.0

    # Tối ưu tốc độ - Giảm mạnh số frame
    frames_per_scene_fast:  int = 1
    frames_per_scene_high:  int = 1
    frames_per_scene_ultra: int = 1


@dataclass
class AnalysisConfig:
    """Cấu hình phân tích"""

    processing_modes: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "fast": {
            "use_qwen_vl":     True,
            "use_florence":    False,
            "use_internvideo": False,
            "frames_per_scene": 1,
            "use_refinement":  False,
            "batch_size":      1,
        },
        "high": {
            "use_qwen_vl":     True,
            "use_florence":    False,
            "use_internvideo": False,
            "frames_per_scene": 1,          # Giảm để nhanh
            "use_refinement":  True,
            "batch_size":      1,
        },
        "ultra": {
            "use_qwen_vl":     True,
            "use_florence":    False,
            "use_internvideo": False,
            "frames_per_scene": 1,
            "use_refinement":  True,
            "batch_size":      1,
        },
    })

    min_confidence:      float = 0.3
    high_confidence:     float = 0.7
    max_tags_per_frame:  int   = 20
    max_objects_per_frame: int = 25


# Các class còn lại giữ nguyên (SearchConfig, DatabaseConfig, WebConfig, LoggingConfig)
@dataclass
class SearchConfig:
    embedding_dimension: int   = 1024
    top_k_initial:       int   = 30
    top_k_final:         int   = 10
    vector_weight: float = 0.6
    bm25_weight:   float = 0.4
    use_reranker:   bool = False
    reranker_top_k: int  = 5
    min_score:   float = 0.1
    max_results: int   = 50


@dataclass
class DatabaseConfig:
    chroma_persist_dir:    Path = DB_DIR / "chroma"
    sqlite_db_path:        Path = DB_DIR / "metadata.db"
    chroma_collection_name: str = "video_frames"
    enable_wal:            bool = True
    cache_size:            int  = 5000


@dataclass
class WebConfig:
    host:  str  = "0.0.0.0"
    port:  int  = 8000
    debug: bool = True
    reload: bool = True
    max_upload_size: int = 10 * 1024 * 1024 * 1024
    allowed_extensions: set = field(default_factory=lambda: {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"})
    secret_key:      str = "change-this-in-production"
    session_timeout: int = 3600


@dataclass
class LoggingConfig:
    log_level:   str  = "INFO"
    log_format:  str  = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file:    Path = LOGS_DIR / "app.log"
    max_bytes:   int  = 10 * 1024 * 1024
    backup_count: int = 5


class Config:
    def __init__(self):
        self.model    = ModelConfig()
        self.video    = VideoProcessingConfig()
        self.analysis = AnalysisConfig()
        self.search   = SearchConfig()
        self.database = DatabaseConfig()
        self.web      = WebConfig()
        self.logging  = LoggingConfig()
        self.OUTPUT_DIR = OUTPUT_DIR

    def get_processing_mode_config(self, mode: str) -> Dict[str, Any]:
        if mode not in self.analysis.processing_modes:
            raise ValueError(f"Invalid processing mode: {mode}")
        return self.analysis.processing_modes[mode]


# Global instance
config = Config()


def load_env_config():
    if os.getenv("VIDEO_AI_DEBUG"):
        config.web.debug = True
        config.logging.log_level = "DEBUG"
    if os.getenv("VIDEO_AI_PORT"):
        config.web.port = int(os.getenv("VIDEO_AI_PORT"))


load_env_config()