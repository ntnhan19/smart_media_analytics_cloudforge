"""
Repository Layer — CRUD Operations for Database Entities

Provides high-level data access patterns for:
- Videos
- Scenes and Frames
- Transcriptions
- Embeddings and Search Results
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .db_client import DatabaseClient, Repository, QueryBuilder, BatchInsertBuilder
from .db_models import (
    VideoMetadata, Scene, Frame, Transcript, TranscriptionSegment,
    FrameEmbedding, SearchResult, ProcessingStats, SearchQuery,
    VideoStatusEnum, FrameAnalysisTypeEnum, ModelTypeEnum,
    create_video_id, create_scene_id, create_frame_id
)

logger = logging.getLogger(__name__)


class VideoRepository(Repository[VideoMetadata]):
    """Repository for video metadata"""
    
    def __init__(self, db_client: DatabaseClient):
        super().__init__(db_client, "videos")
    
    def create(self, video: VideoMetadata) -> VideoMetadata:
        """Create new video record"""
        logger.info(f"Creating video record: {video.video_id}")
        
        # In production, insert into database
        query = f"""
            INSERT INTO {self.table_name}
            (video_id, file_path, file_name, file_size_mb, duration_sec, width, height,
             fps, total_frames, codec, bitrate_kbps, has_audio, status, processing_mode,
             created_at, updated_at, num_scenes, num_frames, num_frames_analyzed, transcript_length)
            VALUES
            (:video_id, :file_path, :file_name, :file_size_mb, :duration_sec, :width, :height,
             :fps, :total_frames, :codec, :bitrate_kbps, :has_audio, :status, :processing_mode,
             :created_at, :updated_at, :num_scenes, :num_frames, :num_frames_analyzed, :transcript_length)
        """
        
        params = video.to_dict()
        # self.db.execute(query, params)
        
        return video
    
    def read(self, video_id: str) -> Optional[VideoMetadata]:
        """Read video by ID"""
        logger.debug(f"Reading video: {video_id}")
        
        query = QueryBuilder(self.table_name).where("video_id = :video_id", video_id=video_id).build()
        # result = self.db.execute(query, params)
        
        # Convert result to VideoMetadata
        return None  # Placeholder
    
    def update(self, video: VideoMetadata) -> VideoMetadata:
        """Update video record"""
        logger.info(f"Updating video: {video.video_id}")
        
        video.updated_at = datetime.utcnow()
        
        query = f"""
            UPDATE {self.table_name}
            SET file_size_mb = :file_size_mb, status = :status, num_scenes = :num_scenes,
                num_frames = :num_frames, num_frames_analyzed = :num_frames_analyzed,
                transcript_length = :transcript_length, error_message = :error_message,
                updated_at = :updated_at, completed_at = :completed_at
            WHERE video_id = :video_id
        """
        
        params = video.to_dict()
        # self.db.execute(query, params)
        
        return video
    
    def delete(self, video_id: str) -> bool:
        """Delete video record"""
        logger.warning(f"Deleting video: {video_id}")
        
        query = f"DELETE FROM {self.table_name} WHERE video_id = :video_id"
        # self.db.execute(query, {'video_id': video_id})
        
        return True
    
    def list(self, limit: int = 100, offset: int = 0) -> List[VideoMetadata]:
        """List videos with pagination"""
        query = QueryBuilder(self.table_name).order_by("created_at", desc=True).limit(limit).offset(offset).build()
        # results = self.db.execute(query[0], query[1])
        
        return []  # Placeholder
    
    def count(self) -> int:
        """Count total videos"""
        query = f"SELECT COUNT(*) as count FROM {self.table_name}"
        # result = self.db.execute(query)
        
        return 0  # Placeholder
    
    def get_by_status(self, status: VideoStatusEnum, limit: int = 50) -> List[VideoMetadata]:
        """Get videos by processing status"""
        query = QueryBuilder(self.table_name).where("status = :status", status=status.value).limit(limit).build()
        # results = self.db.execute(query[0], query[1])
        
        return []
    
    def get_processing_queue(self, limit: int = 10) -> List[VideoMetadata]:
        """Get videos queued for processing"""
        return self.get_by_status(VideoStatusEnum.QUEUED, limit=limit)
    
    def mark_processing(self, video_id: str) -> VideoMetadata:
        """Mark video as processing"""
        video = self.read(video_id)
        if video:
            video.status = VideoStatusEnum.PROCESSING
            video.updated_at = datetime.utcnow()
            self.update(video)
        return video
    
    def mark_completed(self, video_id: str, stats: Dict[str, Any] = None) -> VideoMetadata:
        """Mark video as completed"""
        video = self.read(video_id)
        if video:
            video.status = VideoStatusEnum.COMPLETED
            video.completed_at = datetime.utcnow()
            if stats:
                video.num_scenes = stats.get('num_scenes', 0)
                video.num_frames = stats.get('num_frames', 0)
                video.num_frames_analyzed = stats.get('num_frames_analyzed', 0)
                video.transcript_length = stats.get('transcript_length', 0)
            self.update(video)
        return video
    
    def mark_failed(self, video_id: str, error: str) -> VideoMetadata:
        """Mark video as failed"""
        video = self.read(video_id)
        if video:
            video.status = VideoStatusEnum.FAILED
            video.error_message = error
            video.error_timestamp = datetime.utcnow()
            self.update(video)
        return video


class SceneRepository(Repository[Scene]):
    """Repository for scene data"""
    
    def __init__(self, db_client: DatabaseClient):
        super().__init__(db_client, "scenes")
    
    def create(self, scene: Scene) -> Scene:
        """Create scene record"""
        logger.debug(f"Creating scene: {scene.scene_id}")
        
        query = f"""
            INSERT INTO {self.table_name}
            (scene_id, video_id, scene_index, start_time_sec, end_time_sec, duration_sec,
             midpoint_sec, keyframe_count, has_keyframes, analysis_type, confidence_score,
             created_at, updated_at)
            VALUES
            (:scene_id, :video_id, :scene_index, :start_time_sec, :end_time_sec, :duration_sec,
             :midpoint_sec, :keyframe_count, :has_keyframes, :analysis_type, :confidence_score,
             :created_at, :updated_at)
        """
        
        params = scene.to_dict()
        # self.db.execute(query, params)
        
        return scene
    
    def read(self, scene_id: str) -> Optional[Scene]:
        """Read scene by ID"""
        query = QueryBuilder(self.table_name).where("scene_id = :scene_id", scene_id=scene_id).build()
        # result = self.db.execute(query[0], query[1])
        
        return None
    
    def update(self, scene: Scene) -> Scene:
        """Update scene"""
        scene.updated_at = datetime.utcnow()
        
        query = f"""
            UPDATE {self.table_name}
            SET keyframe_count = :keyframe_count, has_keyframes = :has_keyframes,
                analysis_type = :analysis_type, confidence_score = :confidence_score,
                updated_at = :updated_at
            WHERE scene_id = :scene_id
        """
        
        params = scene.to_dict()
        # self.db.execute(query, params)
        
        return scene
    
    def delete(self, scene_id: str) -> bool:
        """Delete scene"""
        query = f"DELETE FROM {self.table_name} WHERE scene_id = :scene_id"
        # self.db.execute(query, {'scene_id': scene_id})
        
        return True
    
    def list(self, limit: int = 100, offset: int = 0) -> List[Scene]:
        """List scenes"""
        query = QueryBuilder(self.table_name).limit(limit).offset(offset).build()
        # results = self.db.execute(query[0], query[1])
        
        return []
    
    def count(self) -> int:
        """Count scenes"""
        return 0
    
    def get_by_video(self, video_id: str) -> List[Scene]:
        """Get all scenes for a video"""
        query = QueryBuilder(self.table_name).where("video_id = :video_id", video_id=video_id).order_by("scene_index").build()
        # results = self.db.execute(query[0], query[1])
        
        return []
    
    def batch_create(self, scenes: List[Scene]) -> List[Scene]:
        """Batch create scenes"""
        logger.info(f"Batch creating {len(scenes)} scenes")
        
        builder = BatchInsertBuilder(self.table_name)
        for scene in scenes:
            builder.add_row(scene.to_dict())
        
        batches = builder.build_batches()
        for query, batch_rows in batches:
            # self.db.execute(query, batch_rows)
            pass
        
        return scenes


class FrameRepository(Repository[Frame]):
    """Repository for frame analysis results"""
    
    def __init__(self, db_client: DatabaseClient):
        super().__init__(db_client, "frames")
    
    def create(self, frame: Frame) -> Frame:
        """Create frame record"""
        logger.debug(f"Creating frame: {frame.frame_id}")
        
        query = f"""
            INSERT INTO {self.table_name}
            (frame_id, video_id, scene_id, frame_index, timestamp_sec, keyframe_path,
             vision_analysis, refined_analysis, models_used, inference_time_ms,
             created_at, updated_at)
            VALUES
            (:frame_id, :video_id, :scene_id, :frame_index, :timestamp_sec, :keyframe_path,
             :vision_analysis, :refined_analysis, :models_used, :inference_time_ms,
             :created_at, :updated_at)
        """
        
        params = frame.to_dict()
        # self.db.execute(query, params)
        
        return frame
    
    def read(self, frame_id: str) -> Optional[Frame]:
        """Read frame by ID"""
        query = QueryBuilder(self.table_name).where("frame_id = :frame_id", frame_id=frame_id).build()
        # result = self.db.execute(query[0], query[1])
        
        return None
    
    def update(self, frame: Frame) -> Frame:
        """Update frame"""
        frame.updated_at = datetime.utcnow()
        
        query = f"""
            UPDATE {self.table_name}
            SET vision_analysis = :vision_analysis, refined_analysis = :refined_analysis,
                models_used = :models_used, inference_time_ms = :inference_time_ms,
                updated_at = :updated_at
            WHERE frame_id = :frame_id
        """
        
        params = frame.to_dict()
        # self.db.execute(query, params)
        
        return frame
    
    def delete(self, frame_id: str) -> bool:
        """Delete frame"""
        return True
    
    def list(self, limit: int = 100, offset: int = 0) -> List[Frame]:
        """List frames"""
        return []
    
    def count(self) -> int:
        """Count frames"""
        return 0
    
    def get_by_scene(self, scene_id: str) -> List[Frame]:
        """Get all frames in a scene"""
        query = QueryBuilder(self.table_name).where("scene_id = :scene_id", scene_id=scene_id).order_by("frame_index").build()
        # results = self.db.execute(query[0], query[1])
        
        return []
    
    def get_by_video(self, video_id: str) -> List[Frame]:
        """Get all frames for a video"""
        query = QueryBuilder(self.table_name).where("video_id = :video_id", video_id=video_id).limit(1000).build()
        # results = self.db.execute(query[0], query[1])
        
        return []
    
    def batch_create(self, frames: List[Frame]) -> List[Frame]:
        """Batch create frames"""
        logger.info(f"Batch creating {len(frames)} frames")
        
        builder = BatchInsertBuilder(self.table_name, batch_size=100)
        for frame in frames:
            builder.add_row(frame.to_dict())
        
        batches = builder.build_batches()
        for query, batch_rows in batches:
            # self.db.execute(query, batch_rows)
            pass
        
        return frames


class TranscriptRepository(Repository[Transcript]):
    """Repository for transcription data"""
    
    def __init__(self, db_client: DatabaseClient):
        super().__init__(db_client, "transcripts")
    
    def create(self, transcript: Transcript) -> Transcript:
        """Create transcript record"""
        logger.info(f"Creating transcript: {transcript.transcript_id}")
        
        query = f"""
            INSERT INTO {self.table_name}
            (transcript_id, video_id, full_text, language, duration_sec, num_words,
             num_segments, avg_confidence, whisper_model, created_at, updated_at)
            VALUES
            (:transcript_id, :video_id, :full_text, :language, :duration_sec, :num_words,
             :num_segments, :avg_confidence, :whisper_model, :created_at, :updated_at)
        """
        
        params = transcript.to_dict()
        del params['segments']  # Handle separately
        # self.db.execute(query, params)
        
        # Insert segments
        for segment in transcript.segments:
            self._insert_segment(segment)
        
        return transcript
    
    def _insert_segment(self, segment: TranscriptionSegment):
        """Insert transcription segment"""
        query = f"""
            INSERT INTO transcription_segments
            (segment_id, video_id, segment_index, start_time_sec, end_time_sec,
             text, language, language_confidence, confidence_avg, no_speech_prob,
             compression_ratio, words, created_at)
            VALUES
            (:segment_id, :video_id, :segment_index, :start_time_sec, :end_time_sec,
             :text, :language, :language_confidence, :confidence_avg, :no_speech_prob,
             :compression_ratio, :words, :created_at)
        """
        
        params = segment.to_dict()
        # self.db.execute(query, params)
    
    def read(self, transcript_id: str) -> Optional[Transcript]:
        """Read transcript by ID"""
        return None
    
    def update(self, transcript: Transcript) -> Transcript:
        """Update transcript"""
        transcript.updated_at = datetime.utcnow()
        return transcript
    
    def delete(self, transcript_id: str) -> bool:
        """Delete transcript"""
        return True
    
    def list(self, limit: int = 100, offset: int = 0) -> List[Transcript]:
        """List transcripts"""
        return []
    
    def count(self) -> int:
        """Count transcripts"""
        return 0
    
    def get_by_video(self, video_id: str) -> Optional[Transcript]:
        """Get transcript for video"""
        query = QueryBuilder(self.table_name).where("video_id = :video_id", video_id=video_id).build()
        # result = self.db.execute(query[0], query[1])
        
        return None


class SearchRepository:
    """Repository for search queries and results"""
    
    def __init__(self, db_client: DatabaseClient):
        self.db = db_client
    
    def log_search(self, query: SearchQuery) -> SearchQuery:
        """Log search query for analytics"""
        logger.debug(f"Logging search query: {query.query_id}")
        
        table = "search_queries"
        query_str = f"""
            INSERT INTO {table}
            (query_id, query_text, user_id, num_results, top_k_requested, query_time_ms, created_at)
            VALUES
            (:query_id, :query_text, :user_id, :num_results, :top_k_requested, :query_time_ms, :created_at)
        """
        
        params = query.to_dict()
        # self.db.execute(query_str, params)
        
        return query
    
    def store_search_results(self, video_id: str, results: List[SearchResult]) -> bool:
        """Store search results for later retrieval"""
        logger.debug(f"Storing {len(results)} search results for video: {video_id}")
        
        # Could store results in cache or database
        # For now, just log
        
        return True
    
    def get_search_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get search analytics for date range"""
        query = f"""
            SELECT COUNT(*) as total_queries, AVG(query_time_ms) as avg_query_time,
                   MAX(num_results) as max_results
            FROM search_queries
            WHERE created_at >= :start_date AND created_at <= :end_date
        """
        
        params = {'start_date': start_date, 'end_date': end_date}
        # result = self.db.execute(query, params)
        
        return {}


# ── Repository Factory ────────────────────────────────────────────────────

class RepositoryFactory:
    """Factory for creating repositories"""
    
    def __init__(self, db_client: DatabaseClient):
        self.db = db_client
        self._videos = None
        self._scenes = None
        self._frames = None
        self._transcripts = None
        self._search = None
    
    @property
    def videos(self) -> VideoRepository:
        if self._videos is None:
            self._videos = VideoRepository(self.db)
        return self._videos
    
    @property
    def scenes(self) -> SceneRepository:
        if self._scenes is None:
            self._scenes = SceneRepository(self.db)
        return self._scenes
    
    @property
    def frames(self) -> FrameRepository:
        if self._frames is None:
            self._frames = FrameRepository(self.db)
        return self._frames
    
    @property
    def transcripts(self) -> TranscriptRepository:
        if self._transcripts is None:
            self._transcripts = TranscriptRepository(self.db)
        return self._transcripts
    
    @property
    def search(self) -> SearchRepository:
        if self._search is None:
            self._search = SearchRepository(self.db)
        return self._search
