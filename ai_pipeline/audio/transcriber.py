"""
ASR Model - WhisperX for speech recognition
"""

import torch
import whisperx
from pathlib import Path
from typing import Dict, List, Any, Optional

from config import config
from utils.logger import logger, log_model_loading, log_exception


class WhisperXModel:
    """WhisperX model for accurate speech recognition with word-level timestamps"""
    
    def __init__(self, model_size: str = None, device: str = None):
        self.model_size = model_size or config.model.whisper_model
        self.device = device or config.model.device
        self.compute_type = "float16" if config.model.dtype == "float16" else "int8"
        
        self.model = None
        self.model_a = None  # Alignment model
        self.metadata = None
        
        self._load_model()
    
    def _load_model(self):
        """Load WhisperX model"""
        try:
            log_model_loading(f"WhisperX-{self.model_size}", "loading")
            
            # Load Whisper model
            self.model = whisperx.load_model(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                language="en"  # Will auto-detect but can specify
            )
            
            log_model_loading(f"WhisperX-{self.model_size}", "loaded")
            
        except Exception as e:
            log_model_loading(f"WhisperX-{self.model_size}", "failed")
            log_exception(e, "WhisperXModel._load_model")
            raise
    
    def transcribe(
        self,
        audio_path: Path,
        language: str = None,
        batch_size: int = 16
    ) -> Dict[str, Any]:
        """
        Transcribe audio file
        Returns: Dictionary with segments and word-level timestamps
        """
        try:
            logger.info(f"Transcribing audio: {audio_path.name}")
            
            # Load audio
            audio = whisperx.load_audio(str(audio_path))
            
            # Transcribe
            result = self.model.transcribe(
                audio,
                batch_size=batch_size,
                language=language
            )
            
            # Detect language if not specified
            detected_language = result.get("language", "en")
            logger.info(f"Detected language: {detected_language}")
            
            # Load alignment model if needed
            if self.model_a is None or self.metadata is None:
                self.model_a, self.metadata = whisperx.load_align_model(
                    language_code=detected_language,
                    device=self.device
                )
            
            # Align whisper output
            result_aligned = whisperx.align(
                result["segments"],
                self.model_a,
                self.metadata,
                audio,
                self.device,
                return_char_alignments=False
            )
            
            # Extract word-level timestamps
            transcript_data = self._format_transcript(result_aligned)
            
            logger.success(f"Transcription complete: {len(transcript_data['segments'])} segments")
            return transcript_data
            
        except Exception as e:
            log_exception(e, "WhisperXModel.transcribe")
            return {"segments": [], "words": [], "text": ""}
    
    def _format_transcript(self, aligned_result: Dict) -> Dict[str, Any]:
        """Format aligned transcript into structured data"""
        segments = []
        all_words = []
        full_text = []
        
        for segment in aligned_result.get("segments", []):
            segment_data = {
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"].strip()
            }
            
            # Word-level data
            words_in_segment = []
            for word_info in segment.get("words", []):
                word_data = {
                    "word": word_info["word"],
                    "start": word_info.get("start", segment["start"]),
                    "end": word_info.get("end", segment["end"]),
                    "score": word_info.get("score", 1.0)
                }
                words_in_segment.append(word_data)
                all_words.append(word_data)
            
            segment_data["words"] = words_in_segment
            segments.append(segment_data)
            full_text.append(segment_data["text"])
        
        return {
            "segments": segments,
            "words": all_words,
            "text": " ".join(full_text),
            "language": aligned_result.get("language", "unknown")
        }
    
    def get_transcript_at_time(
        self,
        transcript_data: Dict,
        start_time: float,
        end_time: float
    ) -> str:
        """Get transcript text for a specific time range"""
        words = []
        
        for word_info in transcript_data.get("words", []):
            word_start = word_info["start"]
            word_end = word_info["end"]
            
            # Check if word overlaps with time range
            if word_end >= start_time and word_start <= end_time:
                words.append(word_info["word"])
        
        return " ".join(words).strip()
    
    def search_transcript(
        self,
        transcript_data: Dict,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Search for query in transcript
        Returns: List of matches with timestamps
        """
        matches = []
        query_lower = query.lower()
        
        for segment in transcript_data.get("segments", []):
            text_lower = segment["text"].lower()
            
            if query_lower in text_lower:
                matches.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"],
                    "match_query": query
                })
        
        return matches


class TranscriptProcessor:
    """Process and enhance transcripts"""
    
    @staticmethod
    def merge_short_segments(
        segments: List[Dict],
        min_duration: float = 2.0
    ) -> List[Dict]:
        """Merge segments that are too short"""
        if not segments:
            return []
        
        merged = []
        current = segments[0].copy()
        
        for segment in segments[1:]:
            duration = current["end"] - current["start"]
            
            if duration < min_duration:
                # Merge with next segment
                current["end"] = segment["end"]
                current["text"] = current["text"] + " " + segment["text"]
                if "words" in current and "words" in segment:
                    current["words"].extend(segment["words"])
            else:
                merged.append(current)
                current = segment.copy()
        
        merged.append(current)
        return merged
    
    @staticmethod
    def add_punctuation_pauses(segments: List[Dict]) -> List[Dict]:
        """Add pause information based on punctuation"""
        for segment in segments:
            text = segment["text"]
            
            # Determine pause type
            if text.endswith(".") or text.endswith("!") or text.endswith("?"):
                segment["pause_after"] = "long"
            elif text.endswith(",") or text.endswith(";"):
                segment["pause_after"] = "short"
            else:
                segment["pause_after"] = "none"
        
        return segments
    
    @staticmethod
    def extract_keywords(transcript_text: str, top_n: int = 20) -> List[str]:
        """Extract keywords from transcript (simple version)"""
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which',
            'who', 'when', 'where', 'why', 'how'
        }
        
        # Tokenize and filter
        words = transcript_text.lower().split()
        filtered_words = [
            word.strip('.,!?;:') for word in words
            if word.strip('.,!?;:') not in stop_words and len(word) > 3
        ]
        
        # Count frequency
        from collections import Counter
        word_freq = Counter(filtered_words)
        
        # Get top keywords
        keywords = [word for word, count in word_freq.most_common(top_n)]
        return keywords


def create_asr_model() -> WhisperXModel:
    """Factory function to create ASR model"""
    return WhisperXModel()
