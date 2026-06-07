"""
ASR Model - Faster-Whisper (Production Optimized)
- Hỗ trợ word-level timestamps chính xác
- CPU-first, nhẹ, ổn định trên Windows
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import time

from ai_pipeline.config import config
from utils.logger import logger, log_model_loading, log_exception


class WhisperModel:
    """Faster-Whisper ASR Model - High Performance & Reliable"""

    def __init__(self, model_size: str = None):
        self.model_size = model_size or getattr(config.model, 'whisper_model', 'base')
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load Faster-Whisper model với cấu hình tối ưu cho CPU"""
        try:
            import faster_whisper  # lazy import — không crash khi chưa cài
            log_model_loading(f"Faster-Whisper-{self.model_size}", "loading")

            self.model = faster_whisper.WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",           # Tối ưu tốc độ + memory trên CPU
                cpu_threads=0,                 # Auto detect
                num_workers=2,
                download_root=None
            )

            log_model_loading(f"Faster-Whisper-{self.model_size}", "loaded")
            logger.info(f" Faster-Whisper '{self.model_size}' loaded successfully (CPU + int8)")

        except Exception as e:
            log_exception(e, "WhisperModel._load_model")
            raise

    def transcribe(
        self,
        audio_path: Path,
        language: str = None,
        word_timestamps: bool = True,
        beam_size: int = 5,
        vad_filter: bool = True,
    ) -> Dict[str, Any]:
        """Transcribe audio với Faster-Whisper"""
        try:
            start_time = time.time()
            logger.info(f"Transcribing: {audio_path.name}")

            segments, info = self.model.transcribe(
                str(audio_path),
                language=language,
                word_timestamps=word_timestamps,
                beam_size=beam_size,
                vad_filter=vad_filter,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    max_speech_duration_s=30
                ),
                temperature=0.0,          # Greedy decoding cho tính nhất quán
            )

            detected_lang = info.language
            logger.info(f"Detected language: {detected_lang} (prob: {info.language_probability:.3f})")

            transcript_data = self._format_transcript(segments, detected_lang)

            duration = time.time() - start_time
            logger.info(f"Transcription completed in {duration:.2f}s | "
                       f"{len(transcript_data['segments'])} segments")

            return transcript_data

        except Exception as e:
            log_exception(e, "WhisperModel.transcribe")
            return self._get_empty_transcript()

    def _format_transcript(self, segments, language: str) -> Dict[str, Any]:
        """Format output giữ nguyên data contract với pipeline"""
        formatted_segments = []
        all_words = []

        for segment in segments:
            seg_data = {
                "start": float(segment.start),
                "end": float(segment.end),
                "text": segment.text.strip(),
                "words": []
            }

            if hasattr(segment, 'words') and segment.words:
                for word in segment.words:
                    word_data = {
                        "word": word.word.strip(),
                        "start": float(word.start),
                        "end": float(word.end),
                        "score": float(getattr(word, 'probability', 1.0))
                    }
                    seg_data["words"].append(word_data)
                    all_words.append(word_data)

            formatted_segments.append(seg_data)

        full_text = " ".join(s["text"] for s in formatted_segments)

        return {
            "segments": formatted_segments,
            "words": all_words,
            "text": full_text,
            "language": language
        }

    def _get_empty_transcript(self) -> Dict[str, Any]:
        """Fallback khi có lỗi"""
        return {
            "segments": [],
            "words": [],
            "text": "",
            "language": "unknown"
        }

    def get_transcript_at_time(
        self, transcript_data: Dict, start_time: float, end_time: float
    ) -> str:
        """Lấy text theo khoảng thời gian"""
        words = [
            w["word"] for w in transcript_data.get("words", [])
            if w["end"] >= start_time and w["start"] <= end_time
        ]
        return " ".join(words).strip()

    def search_transcript(
        self, transcript_data: Dict, query: str
    ) -> List[Dict[str, Any]]:
        """Tìm kiếm trong transcript"""
        matches = []
        q = query.lower()

        for seg in transcript_data.get("segments", []):
            if q in seg["text"].lower():
                matches.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"],
                    "match_query": query
                })
        return matches

    def unload(self):
        """Unload model"""
        if self.model is not None:
            try:
                del self.model
            except Exception:
                pass
            self.model = None
        logger.info(f"Faster-Whisper model '{self.model_size}' unloaded")


# ── Utility Class ────────────────────────────────────────────────────────────

class TranscriptProcessor:
    """Các hàm xử lý transcript bổ sung"""

    @staticmethod
    def merge_short_segments(segments: List[Dict], min_duration: float = 2.0) -> List[Dict]:
        """Gộp segment quá ngắn"""
        if not segments:
            return []

        merged = []
        current = segments[0].copy()

        for seg in segments[1:]:
            if current["end"] - current["start"] < min_duration:
                current["end"] = seg["end"]
                current["text"] += " " + seg["text"]
                if "words" in current and "words" in seg:
                    current["words"].extend(seg["words"])
            else:
                merged.append(current)
                current = seg.copy()

        merged.append(current)
        return merged

    @staticmethod
    def extract_keywords(text: str, top_n: int = 15) -> List[str]:
        """Trích xuất từ khóa đơn giản"""
        if not text:
            return []

        stop_words = {'the','a','an','and','or','but','in','on','at','to','for','of','with',
                     'by','from','as','is','was','are','were','be','have','has','this','that'}

        words = [w.strip('.,!?;:') for w in text.lower().split() 
                if w.strip('.,!?;:') not in stop_words and len(w) > 3]

        from collections import Counter
        return [word for word, _ in Counter(words).most_common(top_n)]


# Factory
def create_asr_model() -> WhisperModel:
    return WhisperModel()