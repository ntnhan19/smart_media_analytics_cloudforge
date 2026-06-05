"""
Video Analysis Pipeline
Main pipeline orchestrating video processing và analysis
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime
from PIL import Image

from ai_pipeline.config import config
from utils.logger import logger, ProgressTracker
from ai_pipeline.scene_detection.scene_detector import VideoProcessor, SceneDetector, KeyframeExtractor
from ai_pipeline.vision.vision_models import ModelManager
from ai_pipeline.database.db_client import get_db_client
from ai_pipeline.database.vectordb_client import get_vector_db_client
from ai_pipeline.audio.transcriber import create_asr_model
from ai_pipeline.models.refinement_llm import create_refinement_llm
from ai_pipeline.embeddings.embedding_models import EmbeddingManager
from pathlib import Path as PathlibPath


class SimpleFileManager:
    """Simple file manager for organizing output files"""
    
    def __init__(self, video_id: str, output_dir: Path):
        self.video_id = video_id
        self.output_dir = Path(output_dir)
        self.video_dir = self.output_dir / video_id
        self.video_dir.mkdir(parents=True, exist_ok=True)
        
        self.proxy_path = self.video_dir / "proxy.mp4"
        self.audio_path = self.video_dir / "audio.wav"
        self.keyframes_dir = self.video_dir / "keyframes"
        self.keyframes_dir.mkdir(parents=True, exist_ok=True)

class VideoAnalysisPipeline:
    """Main pipeline for video analysis"""
    
    def __init__(self, processing_mode: str = "fast"):
        self.processing_mode = processing_mode
        self.mode_config = config.get_processing_mode_config(processing_mode)
        
        # Initialize components
        self.video_processor = VideoProcessor()
        self.scene_detector = SceneDetector()
        self.keyframe_extractor = KeyframeExtractor()
        
        # Database
        self.db = get_db_client()
        self.vector_db = get_vector_db_client()
        
        if self.vector_db is None:
            logger.warning("Vector database not available. Embeddings will not be stored.")
        
        # Models (lazy loading)
        self.model_manager = None
        self.asr_model = None
        self.refinement_llm = None
        self.embedding_manager = None
        
        self.video_id = None
        self.file_manager = None
    
    def process_video(
        self,
        video_path: Path,
        video_id: str = None
    ) -> Dict[str, Any]:
        """
        Main entry point - process entire video
        
        Returns:
            {
                'video_id': str,
                'status': 'success' | 'failed',
                'stats': {...},
                'error': str (if failed)
            }
        """
        try:
            logger.section(f"Processing Video - Mode: {self.processing_mode}")
            
            # Generate video ID
            self.video_id = video_id or self._generate_video_id()
            logger.info(f"Video ID: {self.video_id}")
            
            # Setup file manager
            self.file_manager = SimpleFileManager(self.video_id, config.OUTPUT_DIR)
            
            # Initialize progress tracker
            total_steps = 8 if self.mode_config['use_refinement'] else 7
            progress = ProgressTracker(total_steps, "Video Processing")
            
            # Step 1: Video info & validation 
            progress.step("Extracting video information")
            video_info = self._extract_video_info(video_path)
            
            # Step 2: Create proxy video
            progress.step("Creating proxy video")
            proxy_path = self._create_proxy(video_path)
            
            # Step 3: Extract audio & transcribe
            progress.step("Extracting and transcribing audio")
            transcript_data = self._process_audio(video_path)
            
            # Step 4: Scene detection
            progress.step("Detecting scenes")
            scenes = self._detect_scenes(proxy_path or video_path)
            
            # Step 5: Extract keyframes
            progress.step("Extracting keyframes")
            keyframes = self._extract_keyframes(
                proxy_path or video_path,
                scenes
            )
            
            # Step 6: Load models
            progress.step("Loading AI models")
            self._load_models()
            
            # Step 7: Analyze frames
            progress.step(f"Analyzing {len(keyframes)} frames")
            frame_analyses = self._analyze_frames(keyframes)
            
            # Step 8: Refine analysis (optional)
            if self.mode_config['use_refinement']:
                progress.step("Refining analysis with LLM")
                frame_analyses = self._refine_analyses(frame_analyses)
            
            # Giải phóng VRAM hoàn toàn trước khi chạy Embedding Model
            if self.model_manager:
                logger.info("Unloading Vision models to free VRAM for Embeddings...")
                self.model_manager.unload_all()
                self.model_manager = None

            # Step 9: Generate embeddings & store
            progress.step("Generating embeddings and storing")
            self._store_results(
                video_info,
                scenes,
                keyframes,
                frame_analyses,
                transcript_data
            )
            
            # Update video status
            self.db.update_video_status(self.video_id, 'completed')
            
            progress.complete(f"Video processing complete: {self.video_id}")
            
            # Gather stats
            stats = self._gather_stats(scenes, keyframes, frame_analyses)
            
            return {
                'video_id': self.video_id,
                'status': 'success',
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            if self.video_id:
                self.db.update_video_status(self.video_id, 'failed')
            
            return {
                'video_id': self.video_id,
                'status': 'failed',
                'error': str(e)
            }
        
        finally:
            # Cleanup
            self._cleanup()
    
    def _generate_video_id(self) -> str:
        """Generate unique video ID"""
        return f"vid_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    def _extract_video_info(self, video_path: Path) -> Dict[str, Any]:
        """Extract and store video metadata"""
        from ai_pipeline.core.video_processor import VideoInfo
        
        video_info = VideoInfo(video_path)
        info_dict = video_info.to_dict()
        
        # Store in database
        video_data = {
            'video_id': self.video_id,
            'filename': video_path.name,
            'original_path': str(video_path),
            'processing_mode': self.processing_mode,
            **info_dict
        }
        
        self.db.insert_video(video_data)
        
        return info_dict
    
    def _create_proxy(self, video_path: Path) -> Optional[Path]:
        """Create proxy video"""
        try:
            proxy_path = self.file_manager.proxy_path
            success = self.video_processor.create_proxy(video_path, proxy_path)
            
            if success:
                return proxy_path
            return None
            
        except Exception as e:
            logger.warning(f"Proxy creation failed: {e}")
            return None
    
    def _process_audio(self, video_path: Path) -> Optional[Dict]:
        """Extract audio and transcribe"""
        try:
            # Extract audio
            logger.info("Step 1: Extracting audio from video...")
            audio_path = self.file_manager.audio_path
            success = self.video_processor.extract_audio(video_path, audio_path)
            
            if not success or not audio_path.exists():
                logger.warning("No audio track found")
                return None
            
            logger.info(f"Step 2: Audio extracted. Path: {audio_path}")
            
            # Transcribe with WhisperX
            logger.info("Step 3: Initializing WhisperX model...")
            if self.asr_model is None:
                self.asr_model = create_asr_model()
            
            logger.info(f"Step 4: Starting transcription...")
            transcript_data = self.asr_model.transcribe(audio_path)
            logger.info(f"Step 5: Transcription completed. Segments: {len(transcript_data.get('segments', []))}")
            
            # Store transcript in database
            logger.info("Step 6: Storing transcript in database...")
            for idx, segment in enumerate(transcript_data.get('segments', [])):
                self.db.insert_transcript_segment({
                    'video_id': self.video_id,
                    'segment_id': idx,
                    'start_time': segment['start'],
                    'end_time': segment['end'],
                    'text': segment['text'],
                    'words': segment.get('words', []),
                    'language': transcript_data.get('language', 'unknown')
                })
            
            logger.info("Step 7: Audio processing complete")
            return transcript_data
            
        except Exception as e:
            logger.error(f"Audio processing failed: {e}", exc_info=True)
            import traceback
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            return None
    
    def _detect_scenes(self, video_path: Path) -> List[tuple]:
        """
        Detect scene boundaries.
        Returns (start_sec, end_sec) tuples for downstream KeyframeExtractor.
        SceneData objects (with keyframe_path) are also stored in the DB.
        """
        # detect_scenes() returns List[SceneData] — richer data contract
        scene_data_list = self.scene_detector.detect_scenes(video_path)

        # Store scenes + keyframe paths in database
        for sd in scene_data_list:
            self.db.insert_scene({
                'video_id':      self.video_id,
                'scene_id':      sd.scene_index,
                'start_time':    sd.start_time_sec,
                'end_time':      sd.end_time_sec,
                'keyframe_path': sd.keyframe_path,
            })

        # Return tuple list for KeyframeExtractor (backward-compat)
        scenes = [(sd.start_time_sec, sd.end_time_sec) for sd in scene_data_list]
        
        return scenes
    
    def _extract_keyframes(
        self,
        video_path: Path,
        scenes: List[tuple]
    ) -> List[Dict]:
        """Extract keyframes from scenes"""
        frames_per_scene = self.mode_config['frames_per_scene']
        
        keyframes = self.keyframe_extractor.extract_keyframes_from_scenes(
            video_path,
            scenes,
            self.file_manager.keyframes_dir,
            frames_per_scene=frames_per_scene
        )
        
        return keyframes
    
    def _load_models(self):
        """Load AI models based on mode"""
        logger.info("Loading AI models...")
        
        # Free memory from previous models before loading new ones
        if self.asr_model is not None:
            try:
                logger.info("Unloading ASR model to free memory...")
                self.asr_model.unload()
            except Exception as e:
                logger.warning(f"Error unloading ASR model: {e}")
            self.asr_model = None
        
        # Vision models
        self.model_manager = ModelManager()
        self.model_manager.load_models_for_mode(self.processing_mode)
        
        # Refinement LLM
        if self.mode_config['use_refinement']:
            self.refinement_llm = create_refinement_llm()
        
        # Embedding model (after unloading previous models)
        self.embedding_manager = EmbeddingManager()
        self.embedding_manager.load_all()
    
    def _analyze_frames(self, keyframes: List[Dict]) -> List[Dict]:
        """Phân tích khung hình với concurrency - Tối ưu cho GTX 1650"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading
        
        analyses = [None] * len(keyframes)   # Giữ thứ tự sẵn
        total_frames = len(keyframes)
        logger.info(f"Phan tich {total_frames} keyframes | MAX_WORKERS=1")

        MAX_WORKERS = 1
        semaphore = threading.Semaphore(MAX_WORKERS)

        def _safe_analyze(idx, kf):
            with semaphore:
                try:
                    analysis = self._analyze_single_frame(kf)
                    analyses[idx] = analysis
                    if (idx + 1) % 3 == 0 or (idx + 1) == total_frames:
                        logger.info(f"Da phan tich {idx + 1}/{total_frames} frames")
                except Exception as e:
                    logger.error(f"Lỗi frame {idx}: {e}")
                    analyses[idx] = {
                        'keyframe': kf,
                        'vision_outputs': {'error': str(e)}
                    }

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(_safe_analyze, i, kf) for i, kf in enumerate(keyframes)]
            for future in as_completed(futures):
                future.result()  # Để bắt exception nếu có

        return analyses
    
    def _analyze_single_frame(self, keyframe: Dict) -> Dict:
        """Analyze single keyframe"""
        frame_path = Path(keyframe['frame_path'])
        image = Image.open(frame_path).convert('RGB')
        
        vision_outputs = {}
        
        # Qwen-VL analysis (giữ lại - quan trọng nhất)
        if self.mode_config['use_qwen_vl'] and self.model_manager.qwen_vl:
            qwen_result = self.model_manager.qwen_vl.analyze_image(image)
            vision_outputs['qwen_vl'] = qwen_result
        
        # ================== TẮT FLORENCE TẠM THỜI ==================
        # if self.mode_config['use_florence'] and self.model_manager.florence:
        #     objects = self.model_manager.florence.detect_objects(image)
        #     captions = self.model_manager.florence.dense_caption(image)
        #     vision_outputs['florence_objects'] = objects
        #     vision_outputs['florence_captions'] = captions
        # ============================================================
        
        return {
            'keyframe': keyframe,
            'vision_outputs': vision_outputs
        }
    
    def _refine_analyses(self, analyses: List[Dict]) -> List[Dict]:
        """Refine analyses with LLM"""
        if not self.refinement_llm:
            return analyses
        
        refined_analyses = []
        
        for analysis in analyses:
            refined = self.refinement_llm.refine_analysis(
                vision_outputs=analysis['vision_outputs'],
                timestamp=analysis['keyframe']['timestamp'],
                scene_id=analysis['keyframe']['scene_id']
            )
            
            analysis['refined_analysis'] = refined
            refined_analyses.append(analysis)
        
        return refined_analyses
    
    def _store_results(
        self,
        video_info: Dict,
        scenes: List[tuple],
        keyframes: List[Dict],
        analyses: List[Dict],
        transcript_data: Optional[Dict]
    ):
        """Store all results in databases"""
        
        # Prepare data for embedding
        texts_to_embed = []
        metadatas = []
        frame_ids = []
        
        for analysis in analyses:
            kf = analysis['keyframe']
            frame_id = f"{self.video_id}_frame_{kf['scene_id']}_{kf['frame_idx']}"
            
            # Get searchable text
            if 'refined_analysis' in analysis:
                searchable_text = analysis['refined_analysis'].get('searchable_text', '')
                if not searchable_text:
                    searchable_text = analysis['refined_analysis'].get('summary', '')
            else:
                # Fallback to raw vision output
                searchable_text = analysis['vision_outputs'].get('qwen_vl', '')
            
            # Prepare metadata
            metadata = {
                'video_id': self.video_id,
                'frame_id': frame_id,
                'timestamp': kf['timestamp'],
                'scene_id': kf['scene_id'],
                'frame_path': kf['frame_path']
            }
            
            texts_to_embed.append(searchable_text)
            metadatas.append(metadata)
            frame_ids.append(frame_id)
            
            # Store frame in SQLite
            frame_data = {
                'video_id': self.video_id,
                'scene_id': kf['scene_id'],
                'frame_id': frame_id,
                'timestamp': kf['timestamp'],
                'frame_path': kf['frame_path'],
                'searchable_text': searchable_text,
                'refined_analysis': analysis.get('refined_analysis', {}),
                'metadata': analysis.get('vision_outputs', {})
            }
            
            self.db.insert_frame(frame_data)
        
        # Generate embeddings
        if texts_to_embed:
            logger.info("Generating embeddings...")
            embeddings = self.embedding_manager.encode(texts_to_embed)
            
            # Store in ChromaDB if available
            if self.vector_db is not None:
                success = self.vector_db.add_embeddings(
                    embeddings=embeddings,
                    documents=texts_to_embed,
                    metadatas=metadatas,
                    ids=frame_ids
                )
                if success:
                    logger.info(f"Stored {len(embeddings)} embeddings in ChromaDB")
                else:
                    logger.warning("Failed to store embeddings in ChromaDB")
            else:
                logger.warning("Vector database not available, embeddings not stored in ChromaDB")
                logger.info("Embeddings have been computed but not persisted to vector store")
    
    def _gather_stats(
        self,
        scenes: List[tuple],
        keyframes: List[Dict],
        analyses: List[Dict]
    ) -> Dict[str, Any]:
        """Gather processing statistics"""
        return {
            'num_scenes': len(scenes),
            'num_keyframes': len(keyframes),
            'num_analyses': len(analyses),
            'processing_mode': self.processing_mode,
            'models_used': list(self.model_manager.loaded_models) if self.model_manager else []
        }
    
    def _cleanup(self):
        """Cleanup resources"""
        if self.model_manager:
            try:
                self.model_manager.unload_all()
            except Exception as e:
                logger.warning(f"Error during model_manager cleanup: {e}")
            finally:
                self.model_manager = None

        if self.embedding_manager:
            try:
                self.embedding_manager.unload_all()
            except Exception as e:
                logger.warning(f"Error during embedding_manager cleanup: {e}")
            finally:
                self.embedding_manager = None

        if self.asr_model:
            try:
                self.asr_model.unload()
            except Exception as e:
                logger.warning(f"Error during asr_model cleanup: {e}")
            finally:
                self.asr_model = None

        if self.refinement_llm:
            try:
                self.refinement_llm.unload()
            except Exception as e:
                logger.warning(f"Error during refinement_llm cleanup: {e}")
            finally:
                self.refinement_llm = None


def process_video(
    video_path: Path,
    processing_mode: str = "fast",
    video_id: str = None
) -> Dict[str, Any]:
    """
    Convenience function to process a video
    """
    pipeline = VideoAnalysisPipeline(processing_mode=processing_mode)
    return pipeline.process_video(video_path, video_id)
