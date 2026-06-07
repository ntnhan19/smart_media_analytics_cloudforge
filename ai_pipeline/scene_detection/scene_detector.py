"""
Video Processing Utilities
Xử lý video với FFmpeg, keyframe extraction, scene detection
"""

import subprocess
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import cv2
import numpy as np
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector

from ai_pipeline.config import config, THUMBNAILS_DIR
from utils.logger import logger, log_exception


# ── Data contract ─────────────────────────────────────────────────────────────

@dataclass
class SceneData:
    """
    Structured scene metadata — data contract shared with vision tagger
    and transcript aligner for ChromaDB ingestion.
    """
    scene_index:    int
    start_time_sec: float
    end_time_sec:   float
    keyframe_path:  str   # absolute path to JPEG on disk

    @property
    def duration(self) -> float:
        return self.end_time_sec - self.start_time_sec

    @property
    def midpoint(self) -> float:
        return (self.start_time_sec + self.end_time_sec) / 2


class VideoInfo:
    """Class chứa thông tin video"""
    
    def __init__(self, path: Path):
        self.path = path
        self.duration: float = 0.0
        self.width: int = 0
        self.height: int = 0
        self.fps: float = 0.0
        self.total_frames: int = 0
        self.codec: str = ""
        self.bitrate: int = 0
        self.size_mb: float = 0.0
        self.has_audio: bool = False
        
        self._probe()
    
    def _probe(self):
        """Probe video để lấy metadata"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(self.path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            
            # Tìm video stream
            video_stream = None
            audio_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video' and not video_stream:
                    video_stream = stream
                elif stream.get('codec_type') == 'audio' and not audio_stream:
                    audio_stream = stream
            
            if video_stream:
                self.width = int(video_stream.get('width', 0))
                self.height = int(video_stream.get('height', 0))
                self.codec = video_stream.get('codec_name', 'unknown')
                
                # FPS
                fps_str = video_stream.get('r_frame_rate', '0/1')
                if '/' in fps_str:
                    num, den = map(int, fps_str.split('/'))
                    self.fps = num / den if den > 0 else 0.0
                else:
                    self.fps = float(fps_str)
                
                # Total frames
                nb_frames = video_stream.get('nb_frames')
                if nb_frames:
                    self.total_frames = int(nb_frames)
                elif self.fps > 0:
                    format_data = data.get('format', {})
                    self.duration = float(format_data.get('duration', 0))
                    self.total_frames = int(self.duration * self.fps)
            
            # Format info
            format_data = data.get('format', {})
            self.duration = float(format_data.get('duration', 0))
            self.bitrate = int(format_data.get('bit_rate', 0))
            self.size_mb = int(format_data.get('size', 0)) / (1024 * 1024)
            
            # Audio check
            self.has_audio = audio_stream is not None
            
            logger.info(f"Video info: {self.width}x{self.height}, {self.fps:.2f}fps, {self.duration:.2f}s")
            
        except Exception as e:
            log_exception(e, "VideoInfo._probe")
            raise
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'path': str(self.path),
            'duration': self.duration,
            'width': self.width,
            'height': self.height,
            'fps': self.fps,
            'total_frames': self.total_frames,
            'codec': self.codec,
            'bitrate': self.bitrate,
            'size_mb': self.size_mb,
            'has_audio': self.has_audio
        }


class VideoProcessor:
    """Main video processor class"""
    
    def __init__(self):
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Kiểm tra FFmpeg có sẵn"""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, check=True)
            subprocess.run(['ffprobe', '-version'], 
                         capture_output=True, check=True)
            logger.info("FFmpeg found")
        except Exception as e:
            logger.error("FFmpeg not found. Please install FFmpeg.")
            raise
    
    def create_proxy(self, input_path: Path, output_path: Path) -> bool:
        """
        Tạo proxy video với quality thấp hơn để xử lý nhanh
        """
        try:
            logger.info(f"Creating proxy video: {output_path.name}")
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            cmd = [
                'ffmpeg',
                '-i', str(input_path),
                '-vf', f'scale=-2:{config.video.proxy_height}',
                '-c:v', 'libx264',
                '-preset', config.video.proxy_preset,
                '-crf', str(config.video.proxy_crf),
                '-c:a', 'aac',
                '-b:a', '128k',
                '-y',
                str(output_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.success(f"Proxy created: {output_path.name}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            return False
        except Exception as e:
            log_exception(e, "create_proxy")
            return False
    
    def extract_audio(self, input_path: Path, output_path: Path) -> bool:
        """Extract audio track từ video"""
        try:
            logger.info(f"Extracting audio: {output_path.name}")
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            cmd = [
                'ffmpeg',
                '-i', str(input_path),
                '-vn',  # No video
                '-acodec', 'pcm_s16le',
                '-ar', '16000',  # 16kHz for Whisper
                '-ac', '1',  # Mono
                '-y',
                str(output_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.success(f"Audio extracted: {output_path.name}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            return False
        except Exception as e:
            log_exception(e, "extract_audio")
            return False
    
    def extract_thumbnail(self, input_path: Path, output_path: Path, 
                         timestamp: float = 1.0) -> bool:
        """Extract thumbnail tại timestamp cụ thể"""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            cmd = [
                'ffmpeg',
                '-ss', str(timestamp),
                '-i', str(input_path),
                '-vframes', '1',
                '-q:v', '2',
                '-y',
                str(output_path)
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            return True
            
        except Exception as e:
            log_exception(e, "extract_thumbnail")
            return False
    
    def extract_frame_at_time(self, input_path: Path, timestamp: float) -> Optional[np.ndarray]:
        """Extract một frame tại timestamp cụ thể"""
        try:
            cap = cv2.VideoCapture(str(input_path))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_number = int(timestamp * fps)
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return None
            
        except Exception as e:
            log_exception(e, "extract_frame_at_time")
            return None


class SceneDetector:
    """
    Detect scene boundaries trong video và extract representative keyframes.
    Returns structured SceneData objects matching the data contract for
    downstream vision tagger and transcript aligner.
    """

    THUMBNAILS_DIR         = Path("/app/data/thumbnails")   # production path
    FALLBACK_THUMBNAILS_DIR = THUMBNAILS_DIR                # local dev path

    def __init__(
        self,
        threshold: float = None,
        min_scene_length: float = None,
        thumbnails_dir: Path = None
    ):
        self.threshold = threshold or config.video.scene_threshold
        self.min_scene_length = min_scene_length or config.video.min_scene_length

        # /app/data/thumbnails in container, project thumbnails/ locally
        if thumbnails_dir:
            self.thumbnails_dir = thumbnails_dir
        elif self.THUMBNAILS_DIR.parent.exists():
            self.thumbnails_dir = self.THUMBNAILS_DIR
        else:
            self.thumbnails_dir = self.FALLBACK_THUMBNAILS_DIR

        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)

    # ── Public API ─────────────────────────────────────────────────────────────

    def detect_scenes(self, video_path: Path) -> List["SceneData"]:
        """
        Detect scenes and extract one keyframe per scene at midpoint.

        Returns:
            List of SceneData objects (one per scene).
            Falls back to a single scene spanning full duration when fewer
            than 3 scenes are detected (static camera / no cuts).

        Raises:
            FileNotFoundError: if video_path does not exist.
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        logger.info(f"Detecting scenes in: {video_path.name}")

        raw_scenes = self._run_scene_detection(video_path)

        # ── Fallback: < 3 raw scenes → treat whole video as 1 scene ──────────
        if len(raw_scenes) < 3:
            duration = self._get_duration(video_path)
            logger.info(
                f"Only {len(raw_scenes)} raw scene(s) found "
                f"— applying full-video fallback (1 scene, {duration:.2f}s)"
            )
            raw_scenes = [(0.0, duration)]

        # ── Build SceneData list ──────────────────────────────────────────────
        scene_data_list: List["SceneData"] = []
        for idx, (start, end) in enumerate(raw_scenes):
            mid = (start + end) / 2
            kf_path = self.extract_keyframe(
                video_path,
                timestamp_sec=mid,
                output_path=self.thumbnails_dir / f"{video_path.stem}_scene{idx:04d}.jpg"
            )
            scene_data_list.append(SceneData(
                scene_index=idx,
                start_time_sec=start,
                end_time_sec=end,
                keyframe_path=kf_path
            ))

        # ── INFO logging: count + average duration ────────────────────────────
        n = len(scene_data_list)
        durations = [s.duration for s in scene_data_list]
        avg_dur = sum(durations) / n if n else 0.0
        logger.info(
            f"Scenes detected: {n} | "
            f"Avg duration: {avg_dur:.2f}s | "
            f"Total: {sum(durations):.2f}s"
        )

        return scene_data_list

    def extract_keyframe(
        self,
        video_path: Path,
        timestamp_sec: float,
        output_path: Path
    ) -> str:
        """
        Extract a single JPEG frame at timestamp_sec.

        Returns:
            Absolute path string of the written JPEG, or "" on failure.

        cv2.VideoCapture is always released via finally block (no memory leak).
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(str(video_path))
        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            frame_number = int(timestamp_sec * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()

            if not ret:
                # Safety: try one frame earlier
                cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_number - 1))
                ret, frame = cap.read()

            if ret:
                cv2.imwrite(str(output_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                logger.debug(f"Keyframe saved: {output_path.name} @ {timestamp_sec:.2f}s")
                return str(output_path.resolve())

            logger.warning(
                f"Could not read frame at {timestamp_sec:.2f}s from {video_path.name}"
            )
            return ""

        finally:
            cap.release()   # Always release — no memory leak

    # ── Private helpers ────────────────────────────────────────────────────────

    def _run_scene_detection(self, video_path: Path) -> List[Tuple[float, float]]:
        """Run PySceneDetect; return (start_sec, end_sec) tuples."""
        try:
            video = open_video(str(video_path))
            scene_manager = SceneManager()
            scene_manager.add_detector(
                ContentDetector(
                    threshold=self.threshold,
                    min_scene_len=int(
                        self.min_scene_length * video.frame_rate
                    )
                )
            )
            scene_manager.detect_scenes(video)
            scene_list = scene_manager.get_scene_list()

            return [(s[0].get_seconds(), s[1].get_seconds()) for s in scene_list]

        except Exception as e:
            log_exception(e, "_run_scene_detection")
            return []

    def _get_duration(self, video_path: Path) -> float:
        """Return video duration in seconds via cv2."""
        cap = cv2.VideoCapture(str(video_path))
        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            total = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            return total / fps if total > 0 else 0.0
        finally:
            cap.release()

    # ── Backward-compatible tuple API ──────────────────────────────────────────

    def detect_scenes_as_tuples(self, video_path: Path) -> List[Tuple[float, float]]:
        """
        Returns (start_sec, end_sec) tuples.
        Used by KeyframeExtractor and VideoAnalysisPipeline.
        """
        return [(s.start_time_sec, s.end_time_sec) for s in self.detect_scenes(video_path)]


class KeyframeExtractor:
    """Extract keyframes từ video"""
    
    def __init__(self):
        self.processor = VideoProcessor()
    
    def extract_keyframes_from_scenes(
        self, 
        video_path: Path, 
        scenes: List[Tuple[float, float]],
        output_dir: Path,
        frames_per_scene: int = 3
    ) -> List[Dict]:
        """
        Extract keyframes từ mỗi scene
        Returns: List of {frame_path, timestamp, scene_id}
        """
        try:
            logger.info(f"Extracting keyframes: {frames_per_scene} per scene")
            
            output_dir.mkdir(parents=True, exist_ok=True)
            keyframes = []
            
            cap = cv2.VideoCapture(str(video_path))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            for scene_id, (start_time, end_time) in enumerate(scenes):
                scene_duration = end_time - start_time
                
                # Tính timestamps để extract
                if frames_per_scene == 1:
                    timestamps = [start_time + scene_duration / 2]
                else:
                    timestamps = [
                        start_time + scene_duration * i / (frames_per_scene - 1)
                        for i in range(frames_per_scene)
                    ]
                
                # Extract frames
                for frame_idx, timestamp in enumerate(timestamps):
                    frame_number = int(timestamp * fps)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                    ret, frame = cap.read()
                    
                    if ret:
                        # Save frame
                        frame_filename = f"scene_{scene_id:04d}_frame_{frame_idx:02d}.jpg"
                        frame_path = output_dir / frame_filename
                        
                        cv2.imwrite(
                            str(frame_path), 
                            frame,
                            [cv2.IMWRITE_JPEG_QUALITY, 95]
                        )
                        
                        keyframes.append({
                            'frame_path': str(frame_path),
                            'timestamp': timestamp,
                            'scene_id': scene_id,
                            'frame_idx': frame_idx
                        })
            
            cap.release()
            logger.success(f"Extracted {len(keyframes)} keyframes")
            return keyframes
            
        except Exception as e:
            log_exception(e, "extract_keyframes_from_scenes")
            return []
    
    def extract_uniform_keyframes(
        self,
        video_path: Path,
        output_dir: Path,
        interval_seconds: float = 1.0
    ) -> List[Dict]:
        """Extract keyframes với interval đều"""
        try:
            video_info = VideoInfo(video_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            keyframes = []
            cap = cv2.VideoCapture(str(video_path))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            timestamp = 0.0
            frame_idx = 0
            
            while timestamp < video_info.duration:
                frame_number = int(timestamp * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = cap.read()
                
                if ret:
                    frame_filename = f"frame_{frame_idx:06d}.jpg"
                    frame_path = output_dir / frame_filename
                    
                    cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                    
                    keyframes.append({
                        'frame_path': str(frame_path),
                        'timestamp': timestamp,
                        'frame_idx': frame_idx
                    })
                    
                    frame_idx += 1
                
                timestamp += interval_seconds
            
            cap.release()
            logger.success(f"Extracted {len(keyframes)} uniform keyframes")
            return keyframes
            
        except Exception as e:
            log_exception(e, "extract_uniform_keyframes")
            return []


def get_video_info(video_path: Path) -> VideoInfo:
    """Convenience function to get video info"""
    return VideoInfo(video_path)


def validate_video(video_path: Path) -> Tuple[bool, str]:
    """
    Validate video file
    Returns: (is_valid, error_message)
    """
    try:
        if not video_path.exists():
            return False, "File does not exist"
        
        if video_path.suffix.lower() not in config.web.allowed_extensions:
            return False, f"Unsupported format: {video_path.suffix}"
        
        # Check size
        size_mb = video_path.stat().st_size / (1024 * 1024)
        if size_mb > config.video.max_video_size / (1024 * 1024):
            return False, f"File too large: {size_mb:.1f}MB"
        
        # Probe video
        video_info = VideoInfo(video_path)
        
        if video_info.duration > config.video.max_video_duration:
            return False, f"Video too long: {video_info.duration:.1f}s"
        
        if video_info.width == 0 or video_info.height == 0:
            return False, "Invalid video dimensions"
        
        return True, "OK"
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"
