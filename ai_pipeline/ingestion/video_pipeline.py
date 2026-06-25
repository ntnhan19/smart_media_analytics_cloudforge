"""
Video Analysis Pipeline

End-to-End pipeline xử lý video → Trả về VideoAnalysisContract
Tương thích hoàn toàn với Backend (PostgreSQL + MinIO + Redis)
"""

import os
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── AI Pipeline Modules ─────────────────────────────────────────────────────
from ai_pipeline.ingestion.contracts import (
    DetectedObjectContract,
    ObjectOccurrenceContract,
    SceneAnalysisContract,
    TagContract,
    VideoAnalysisContract,
)

from ai_pipeline.audio.transcriber import create_asr_model
from ai_pipeline.config import config
from ai_pipeline.providers import create_text_embedder, create_vision_provider
from ai_pipeline.models.refinement_llm import create_refinement_llm
from ai_pipeline.scene_detection.scene_detector import (
    KeyframeExtractor,
    SceneDetector,
    VideoInfo,
    VideoProcessor,
)

# ── Utils ───────────────────────────────────────────────────────────────────
from utils.logger import ProgressTracker, logger


class SimpleFileManager:
    """Quản lý file tạm cho một lần xử lý video."""

    def __init__(self, asset_id: str, output_dir: Path):
        self.asset_id = asset_id
        self.output_dir = Path(output_dir)
        self.video_dir = self.output_dir / asset_id
        self.video_dir.mkdir(parents=True, exist_ok=True)

        self.proxy_path = self.video_dir / "proxy.mp4"
        self.audio_path = self.video_dir / "audio.wav"
        self.keyframes_dir = self.video_dir / "keyframes"
        self.keyframes_dir.mkdir(parents=True, exist_ok=True)


class VideoAnalysisPipeline:
    """Pipeline chính xử lý video end-to-end."""

    def __init__(
        self,
        processing_mode: str = "fast",
        vision_provider=None,
        text_embedder=None,
        storage_client=None,
        progress_callback=None,
    ):
        self.processing_mode = processing_mode
        self.mode_config = config.get_processing_mode_config(processing_mode)

        # Core processors
        self.video_processor = VideoProcessor()
        self.scene_detector = SceneDetector()
        self.keyframe_extractor = KeyframeExtractor()

        # AI Providers (Abstraction)
        self.vision_provider = vision_provider or create_vision_provider()
        self.text_embedder = text_embedder or create_text_embedder()
        self.refinement_llm = self._init_refinement_llm()

        self.storage_client = storage_client
        self.progress_callback = progress_callback
        self.asr_model = None

    def _init_refinement_llm(self):
        """Khởi tạo Refinement LLM an toàn."""
        try:
            return create_refinement_llm()
        except Exception as e:
            logger.warning(f"Không thể khởi tạo Refinement LLM: {e}. Sử dụng fallback.")
            return None

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def analyze_video(
        self,
        video_path: Path,
        asset_id: Optional[str] = None,
        source_storage_key: Optional[str] = None,
    ) -> VideoAnalysisContract:
        """Phân tích video và trả về contract đầy đủ."""
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video không tồn tại: {video_path}")

        asset_id = asset_id or self._generate_asset_id()
        file_manager = SimpleFileManager(asset_id, config.OUTPUT_DIR)

        logger.section(f"Processing Video - Mode: {self.processing_mode}")
        start_time = time.time()

        progress = ProgressTracker(8, "Video Processing")

        # 1. Video Info
        progress.step("Extracting video information")
        video_info = VideoInfo(video_path)

        # 2. Proxy video
        progress.step("Creating proxy video")
        proxy_path = self._create_proxy(video_path, file_manager.proxy_path)
        working_video = proxy_path or video_path

        # 3. Audio + Transcription
        progress.step("Extracting and transcribing audio")
        transcript_data = self._process_audio(video_path, file_manager.audio_path)

        # 4. Scene Detection
        progress.step("Detecting scenes")
        scene_data = self.scene_detector.detect_scenes(working_video)

        # 5. Keyframe Extraction
        progress.step("Extracting keyframes")
        keyframes = self.keyframe_extractor.extract_keyframes_from_scenes(
            working_video,
            [(s.start_time_sec, s.end_time_sec) for s in scene_data],
            file_manager.keyframes_dir,
            frames_per_scene=self.mode_config.get("frames_per_scene", 1),
        )
        keyframes_by_scene = {int(kf["scene_id"]): kf for kf in keyframes}

        # 6. Captioning + Refinement
        progress.step("Captioning & Refining scenes")
        scene_contracts = self._process_scenes(
            asset_id=asset_id,
            scene_data=scene_data,
            keyframes_by_scene=keyframes_by_scene,
            transcript_data=transcript_data,
        )

        # 7. Upload keyframes
        progress.step("Uploading keyframes")
        self._upload_keyframes(asset_id, scene_contracts)

        # 8. Embedding
        progress.step("Generating embeddings")
        self._embed_scenes(scene_contracts)

        # Build final contract
        analysis = VideoAnalysisContract(
            asset_id=asset_id,
            file_name=video_path.name,
            file_path=source_storage_key or str(video_path),
            media_type="video",
            duration_sec=float(video_info.duration),
            resolution=f"{video_info.width}x{video_info.height}",
            file_size_bytes=int(video_path.stat().st_size),
            full_transcript=transcript_data.get("text", ""),
            transcripts_json=transcript_data.get("segments", []),
            tags=self._aggregate_tags(scene_contracts, transcript_data.get("text", "")),
            scenes=scene_contracts,
        )

        logger.info(f"Pipeline completed in {time.time() - start_time:.2f}s | "
                   f"{len(scene_contracts)} scenes")
        return analysis

    # =========================================================================
    # INTERNAL METHODS
    # =========================================================================

    def _generate_asset_id(self) -> str:
        return f"vid_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    def _create_proxy(self, video_path: Path, proxy_path: Path) -> Optional[Path]:
        try:
            if self.video_processor.create_proxy(video_path, proxy_path):
                return proxy_path
            return None
        except Exception as e:
            logger.warning(f"Proxy creation failed: {e}")
            return None

    def _process_audio(self, video_path: Path, audio_path: Path) -> Dict[str, Any]:
        try:
            if not self.video_processor.extract_audio(video_path, audio_path):
                return {"text": "", "segments": [], "words": []}

            self.asr_model = self.asr_model or create_asr_model()
            return self.asr_model.transcribe(audio_path)
        except Exception as e:
            logger.warning(f"Audio processing failed: {e}")
            return {"text": "", "segments": [], "words": []}

    def _process_scenes(
        self,
        asset_id: str,
        scene_data,
        keyframes_by_scene: Dict[int, Dict],
        transcript_data: Dict[str, Any],
    ) -> List[SceneAnalysisContract]:
        """Xử lý caption + refinement cho từng scene."""
        scenes: List[SceneAnalysisContract] = []

        for scene in scene_data:
            keyframe = keyframes_by_scene.get(scene.scene_index)
            keyframe_path = keyframe["frame_path"] if keyframe else None

            # 1. Raw vision caption (tiếng Anh)
            raw_caption = ""
            if keyframe_path:
                try:
                    raw_caption = self.vision_provider.caption_keyframe(Path(keyframe_path))
                except Exception as e:
                    logger.warning(f"Vision failed scene {scene.scene_index}: {e}")

            # 2. Transcript snippet
            transcript_snippet = self._get_transcript_for_scene(
                transcript_data, scene.start_time_sec, scene.end_time_sec
            )

            # 3. Refinement LLM
            refined = self._refine_scene(
                raw_caption=raw_caption,
                transcript_snippet=transcript_snippet,
                scene_index=scene.scene_index,
                timestamp=scene.start_time_sec,
            )

            # 4. Build Scene Contract
            scene_tags = [
                TagContract(name=tag, category="theme")
                for tag in refined.get("tags", {}).get("scene_tags", [])
                if str(tag).strip()
            ]
            scenes.append(
                SceneAnalysisContract(
                    scene_index=scene.scene_index,
                    timestamp_start_sec=float(scene.start_time_sec),
                    timestamp_end_sec=float(scene.end_time_sec),
                    caption=refined["summary"],
                    transcript_snippet=transcript_snippet,
                    searchable_text=refined.get("searchable_text", ""),
                    keyframe_path=str(keyframe_path) if keyframe_path else "",
                    keyframe_s3_key=f"keyframes/{asset_id}/{scene.scene_index:04d}.jpg",
                    tags=scene_tags,
                )
            )

        return scenes

    def _refine_scene(self, raw_caption: str, transcript_snippet: str, scene_index: int, timestamp: float):
        """Gọi Refinement LLM với fallback an toàn."""
        if not self.refinement_llm:
            return self._make_fallback(scene_index, timestamp, transcript_snippet)

        try:
            result = self.refinement_llm.refine_analysis(
                vision_outputs={"qwen_vl": raw_caption},
                timestamp=timestamp,
                scene_id=scene_index,
                transcript_snippet=transcript_snippet,
            )
            return result
        except Exception as e:
            logger.warning(f"Refinement failed scene {scene_index}: {e}")
            return self._make_fallback(scene_index, timestamp, transcript_snippet)

    @staticmethod
    def _make_fallback(scene_index: int, timestamp: float, transcript: str) -> Dict:
        summary = f"Phân cảnh {scene_index} tại {timestamp:.0f} giây"
        if transcript:
            summary = f"Phân cảnh có lời thoại: {transcript[:180]}"

        return {
            "summary": summary,
            "tags": {"scene_tags": ["video"]},
            "searchable_text": summary,
        }

    def _get_transcript_for_scene(self, transcript_data: Dict, start: float, end: float) -> str:
        """Trích đoạn transcript theo khoảng thời gian scene."""
        segments = transcript_data.get("segments", [])
        texts = []
        for seg in segments:
            if seg.get("end", 0) >= start and seg.get("start", 0) <= end:
                text = seg.get("text", "").strip()
                if text:
                    texts.append(text)
        return " ".join(texts).strip()

    def _upload_keyframes(self, asset_id: str, scenes: List[SceneAnalysisContract]):
        if not self.storage_client:
            return
        for scene in scenes:
            if not scene.keyframe_path or not Path(scene.keyframe_path).exists():
                continue
            remote_key = scene.keyframe_s3_key
            success = self.storage_client.upload_file(scene.keyframe_path, remote_key)
            if not success:
                logger.warning(f"Failed to upload keyframe: {remote_key}")

    def _embed_scenes(self, scenes: List[SceneAnalysisContract]):
        """Sinh embedding cho tất cả scenes."""
        if not scenes:
            return
        texts = [scene.embedding_text for scene in scenes]
        embeddings = self.text_embedder.embed_texts(texts)

        for scene, emb in zip(scenes, embeddings):
            scene.embedding = emb.tolist() if hasattr(emb, "tolist") else emb

    def _aggregate_tags(self, scenes: List[SceneAnalysisContract], full_transcript: str) -> List[TagContract]:
        """Tổng hợp tags cho toàn video."""
        seen = set()
        tags = []

        for scene in scenes:
            for tag in scene.tags:
                key = (tag.name, tag.category)
                if key not in seen:
                    seen.add(key)
                    tags.append(tag)

        # Thêm tag từ full transcript nếu cần
        return tags[:25]

    def _cleanup(self):
        """Dọn dẹp tài nguyên."""
        if self.asr_model:
            try:
                self.asr_model.unload()
            except Exception:
                pass
            self.asr_model = None

        if self.refinement_llm:
            try:
                self.refinement_llm.unload()
            except Exception:
                pass


# =============================================================================
# Shortcut
# =============================================================================

def process_video(video_path: Path, processing_mode: str = "fast", asset_id: Optional[str] = None):
    pipeline = VideoAnalysisPipeline(processing_mode=processing_mode)
    return pipeline.analyze_video(video_path, asset_id=asset_id)
