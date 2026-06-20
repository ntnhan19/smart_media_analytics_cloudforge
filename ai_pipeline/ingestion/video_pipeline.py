"""
Video Analysis Pipeline

Cloud-ready pipeline core. It analyzes local video files and returns a
backend-compatible contract; database persistence belongs to the backend
ingest service.
"""

import os
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ai_pipeline.audio.transcriber import TranscriptProcessor, create_asr_model
from ai_pipeline.config import config
from ai_pipeline.ingestion.contracts import (
    DetectedObjectContract,
    ObjectOccurrenceContract,
    SceneAnalysisContract,
    TagContract,
    VideoAnalysisContract,
)
from ai_pipeline.providers import create_text_embedder, create_vision_provider
from ai_pipeline.models.refinement_llm import create_refinement_llm
from ai_pipeline.scene_detection.scene_detector import (
    KeyframeExtractor,
    SceneDetector,
    VideoInfo,
    VideoProcessor,
)
from utils.logger import ProgressTracker, logger

ProgressCallback = Callable[[str, float], None]


class SimpleFileManager:
    """Organize intermediate files for one video analysis run."""

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
    """Main pipeline for video analysis without direct DB ownership."""

    def __init__(
        self,
        processing_mode: str = "fast",
        vision_provider=None,
        text_embedder=None,
        storage_client=None,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        self.processing_mode = processing_mode
        self.mode_config = config.get_processing_mode_config(processing_mode)
        self.video_processor = VideoProcessor()
        self.scene_detector = SceneDetector()
        self.keyframe_extractor = KeyframeExtractor()
        
        # ── Abstraction Provider Selection (Task 7) ──────────────────────────
        # Tự động switch linh hoạt cấu hình theo biến môi trường hệ thống
        self.vision_provider = vision_provider or create_vision_provider()
        self.text_embedder = text_embedder or create_text_embedder()
        
        self.storage_client = storage_client
        self.progress_callback = progress_callback
        self.asr_model = None
        
        # ✨ Khởi tạo cấu hình Refinement LLM an toàn
        self.refinement_llm = self._init_refinement_llm()

    def _init_refinement_llm(self):
        """Khởi tạo mô hình lọc dữ liệu an toàn dựa trên nhà cung cấp"""
        ai_provider = os.getenv("AI_PROVIDER", "local").lower()
        if ai_provider == "aws":
            logger.info("☁️ Cloud Mode: Khởi chạy Khung Stub AWS Bedrock cho Refinement LLM")
            # Bạn có thể bổ sung class BedrockRefinementLLM(stub) tại đây khi lên AWS Cloud
            return create_refinement_llm() 
        else:
            try:
                return create_refinement_llm()
            except Exception as e:
                logger.warning(f"⚠️ Không thể kết nối Ollama server lúc khởi tạo: {e}. Luồng chạy sẽ kích hoạt fallback.")
                return None

    def process_video(
        self,
        video_path: Path,
        asset_id: Optional[str] = None,
        source_storage_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compatibility wrapper returning a dict result."""
        try:
            analysis = self.analyze_video(
                video_path=video_path,
                asset_id=asset_id,
                source_storage_key=source_storage_key,
            )
            return {
                "asset_id": analysis.asset_id,
                "status": "success",
                "analysis": analysis.to_dict(include_embeddings=True),
                "stats": {
                    "num_scenes": len(analysis.scenes),
                    "processing_mode": self.processing_mode,
                    "full_transcript_length": len(analysis.full_transcript or ""),
                },
            }
        except Exception as exc:
            logger.error(f"Pipeline failed: {exc}", exc_info=True)
            return {
                "asset_id": asset_id,
                "status": "failed",
                "error": str(exc),
            }
        finally:
            self._cleanup()

    def analyze_video(
        self,
        video_path: Path,
        asset_id: Optional[str] = None,
        source_storage_key: Optional[str] = None,
    ) -> VideoAnalysisContract:
        """Analyze a local video file and return the backend data contract."""
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        asset_id = asset_id or self._generate_asset_id()
        file_manager = SimpleFileManager(asset_id, config.OUTPUT_DIR)
        self._publish("metadata", 5.0)

        logger.section(f"Processing Video - Mode: {self.processing_mode}")
        pipeline_start = time.time()

        total_steps = 7
        progress = ProgressTracker(total_steps, "Video Processing")

        progress.step("Extracting video information")
        video_info = VideoInfo(video_path)
        self._publish("metadata", 10.0)

        progress.step("Creating proxy video")
        proxy_path = self._create_proxy(video_path, file_manager.proxy_path)
        working_video = proxy_path or video_path
        self._publish("proxy", 20.0)

        progress.step("Extracting and transcribing audio")
        transcript_data = self._process_audio(video_path, file_manager.audio_path)
        self._publish("transcription", 35.0)

        progress.step("Detecting scenes")
        scene_data = self.scene_detector.detect_scenes(working_video)
        scenes_as_tuples = [(s.start_time_sec, s.end_time_sec) for s in scene_data]
        self._publish("scene_detection", 45.0)

        progress.step("Extracting keyframes")
        keyframes = self.keyframe_extractor.extract_keyframes_from_scenes(
            working_video,
            scenes_as_tuples,
            file_manager.keyframes_dir,
            frames_per_scene=self.mode_config["frames_per_scene"],
        )
        keyframes_by_scene = {int(kf["scene_id"]): kf for kf in keyframes}
        self._publish("keyframe_extraction", 55.0)

        progress.step("Captioning keyframes")
        scene_contracts = self._caption_scenes(
            asset_id=asset_id,
            scene_data=scene_data,
            keyframes_by_scene=keyframes_by_scene,
            transcript_data=transcript_data,
        )
        self._publish("vision_caption", 72.0)

        progress.step("Uploading keyframes")
        self._upload_keyframes(asset_id, scene_contracts)
        self._publish("keyframe_upload", 80.0)

        progress.step("Generating embeddings")
        self._embed_scenes(scene_contracts)
        self._publish("embedding", 92.0)

        asset_tags = self._aggregate_tags(scene_contracts, transcript_data.get("text", ""))
        analysis = VideoAnalysisContract(
            asset_id=asset_id,
            file_name=video_path.name,
            file_path=source_storage_key or str(video_path),
            media_type="video",
            duration_sec=float(video_info.duration),
            resolution=f"{video_info.width}x{video_info.height}",
            file_size_bytes=int(video_path.stat().st_size),
            full_transcript=transcript_data.get("text", ""),
            tags=asset_tags,
            scenes=scene_contracts,
        )

        progress.complete(f"Video processing complete: {asset_id}")
        logger.info(f"Pipeline completed in {time.time() - pipeline_start:.2f}s")
        self._publish("completed_analysis", 100.0)
        return analysis

    def _generate_asset_id(self) -> str:
        return f"vid_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    def _create_proxy(self, video_path: Path, proxy_path: Path) -> Optional[Path]:
        try:
            return proxy_path if self.video_processor.create_proxy(video_path, proxy_path) else None
        except Exception as exc:
            logger.warning(f"Proxy creation failed: {exc}")
            return None

    def _process_audio(self, video_path: Path, audio_path: Path) -> Dict[str, Any]:
        try:
            if not self.video_processor.extract_audio(video_path, audio_path):
                return {"segments": [], "words": [], "text": "", "language": "unknown"}
            self.asr_model = self.asr_model or create_asr_model()
            return self.asr_model.transcribe(audio_path)
        except Exception as exc:
            logger.warning(f"Audio processing failed: {exc}", exc_info=True)
            return {"segments": [], "words": [], "text": "", "language": "unknown"}

    def _caption_scenes(
        self,
        asset_id: str,
        scene_data,
        keyframes_by_scene: Dict[int, Dict[str, Any]],
        transcript_data: Dict[str, Any],
    ) -> List[SceneAnalysisContract]:
        scenes: List[SceneAnalysisContract] = []
        for scene in scene_data:
            keyframe = keyframes_by_scene.get(scene.scene_index)
            keyframe_path = keyframe["frame_path"] if keyframe else scene.keyframe_path
            
            # 1. Trích xuất mô tả thô từ mô hình thị giác máy tính (Llava)
            raw_caption = ""
            if keyframe_path:
                try:
                    raw_caption = self.vision_provider.caption_keyframe(Path(keyframe_path))
                except Exception as ve:
                    logger.warning(f"Vision Captioning failed for scene {scene.scene_index}: {ve}")
            raw_caption = raw_caption or "Video scene with visual content."
            
            # 2. Định vị đoạn phụ đề tương ứng của phân cảnh từ Whisper
            transcript_snippet = self._transcript_for_scene(
                transcript_data,
                scene.start_time_sec,
                scene.end_time_sec,
            )
            
            # Mặc định cấu hình fallback phòng trường hợp server Ollama tắt đột ngột
            final_caption = raw_caption
            tags = []

            # 3. ✨ THỰC THI REFINEMENT: Gọi Qwen2 biên tập lại dữ liệu
            if self.refinement_llm:
                try:
                    logger.info(f"-> Thực thi Ollama Refinement cho phân cảnh index: {scene.scene_index}")
                    refined_json = self.refinement_llm.refine_analysis(
                        vision_outputs={"qwen_vl": raw_caption},
                        timestamp=float(scene.start_time_sec),
                        scene_id=int(scene.scene_index),
                        transcript_snippet=transcript_snippet
                    )
                    final_caption = refined_json.get("summary") or raw_caption
                    scene_tags = refined_json.get("tags", {}).get("scene_tags", [])
                    tags = [TagContract(name=t, category="theme", source="auto") for t in scene_tags]
                except Exception as re_err:
                    logger.warning(f"Refinement failed, fallback activated: {re_err}")

            if not tags:
                tags = self._tags_for_scene(final_caption, transcript_snippet)
                
            detected_objects = self._objects_for_scene(
                tags,
                scene.start_time_sec,
                scene.end_time_sec,
            )
            
            scenes.append(
                SceneAnalysisContract(
                    scene_index=scene.scene_index,
                    timestamp_start_sec=float(scene.start_time_sec),
                    timestamp_end_sec=float(scene.end_time_sec),
                    caption=final_caption,
                    transcript_snippet=transcript_snippet,
                    keyframe_path=keyframe_path or "",
                    keyframe_s3_key=f"keyframes/{asset_id}/{scene.scene_index}.jpg",
                    tags=tags,
                    detected_objects=detected_objects,
                )
            )
        return scenes

    def _upload_keyframes(self, asset_id: str, scenes: List[SceneAnalysisContract]) -> None:
        if not self.storage_client:
            return
        for scene in scenes:
            if not scene.keyframe_path:
                continue
            remote_key = f"keyframes/{asset_id}/{scene.scene_index}.jpg"
            ok = self.storage_client.upload_file(scene.keyframe_path, remote_key)
            if not ok:
                raise RuntimeError(f"Failed to upload keyframe: {remote_key}")
            scene.keyframe_s3_key = remote_key

    def _embed_scenes(self, scenes: List[SceneAnalysisContract]) -> None:
        texts = [scene.embedding_text or scene.caption for scene in scenes]
        embeddings = self.text_embedder.embed_texts(texts)
        for scene, embedding in zip(scenes, embeddings):
            if len(embedding) != self.text_embedder.embedding_dim:
                raise ValueError(
                    f"Expected {self.text_embedder.embedding_dim}-dim embedding, got {len(embedding)}"
                )
            scene.embedding = embedding

    def _transcript_for_scene(
        self,
        transcript_data: Dict[str, Any],
        start_sec: float,
        end_sec: float,
    ) -> str:
        segments = []
        for segment in transcript_data.get("segments", []):
            if float(segment.get("end", 0.0)) >= start_sec and float(segment.get("start", 0.0)) <= end_sec:
                text = segment.get("text", "").strip()
                if text:
                    segments.append(text)
        if segments:
            return " ".join(segments)

        words = [
            word.get("word", "").strip()
            for word in transcript_data.get("words", [])
            if float(word.get("end", 0.0)) >= start_sec
            and float(word.get("start", 0.0)) <= end_sec
        ]
        return " ".join(word for word in words if word)

    def _tags_for_scene(self, caption: str, transcript_snippet: str) -> List[TagContract]:
        text = f"{caption} {transcript_snippet}"
        keywords = TranscriptProcessor.extract_keywords(text, top_n=8)
        tags = [TagContract(name=kw, category="theme", source="auto") for kw in keywords[:6]]
        if "video" not in [tag.name for tag in tags]:
            tags.append(TagContract(name="video", category="content_type", source="auto"))
        return tags

    def _aggregate_tags(
        self,
        scenes: List[SceneAnalysisContract],
        full_transcript: str,
    ) -> List[TagContract]:
        seen = set()
        tags: List[TagContract] = []
        for scene in scenes:
            for tag in scene.tags:
                key = (tag.name, tag.category)
                if key not in seen:
                    seen.add(key)
                    tags.append(tag)
        for keyword in TranscriptProcessor.extract_keywords(full_transcript, top_n=6):
            key = (keyword, "theme")
            if key not in seen:
                tags.append(TagContract(name=keyword, category="theme", source="auto"))
                seen.add(key)
        return tags[:20]

    def _objects_for_scene(
        self,
        tags: List[TagContract],
        start_sec: float,
        end_sec: float,
    ) -> List[DetectedObjectContract]:
        objects: List[DetectedObjectContract] = []
        for tag in tags[:5]:
            normalized = re.sub(r"[^A-Za-z0-9_ -]", "", tag.name).strip()
            if len(normalized) < 3 or tag.category == "content_type":
                continue
            objects.append(
                DetectedObjectContract(
                    name=normalized,
                    occurrences=[
                        ObjectOccurrenceContract(
                            timestamp_start_sec=float(start_sec),
                            timestamp_end_sec=float(end_sec),
                            confidence=0.5,
                        )
                    ],
                )
            )
        return objects

    def _publish(self, current_step: str, progress: float) -> None:
        if self.progress_callback:
            self.progress_callback(current_step, progress)

    def _cleanup(self) -> None:
        if self.asr_model:
            try:
                self.asr_model.unload()
            except Exception as exc:
                logger.warning(f"Error during ASR cleanup: {exc}")
            self.asr_model = None
        
        if hasattr(self, 'refinement_llm') and self.refinement_llm:
            try:
                self.refinement_llm.unload()
            except Exception:
                pass


def process_video(
    video_path: Path,
    processing_mode: str = "fast",
    video_id: Optional[str] = None,
) -> Dict[str, Any]:
    pipeline = VideoAnalysisPipeline(processing_mode=processing_mode)
    return pipeline.process_video(video_path, asset_id=video_id)