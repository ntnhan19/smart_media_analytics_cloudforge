# -*- coding: utf-8 -*-
"""
Audio / ASR Models — Semantic Indexer Ready (CPU Optimized for i7-10700H)
--------------------------------------------------------------------------
Mục tiêu:
- Hỗ trợ Amazon Transcribe chuẩn AWS Serverless
- Faster-Whisper cấu hình luồng an toàn, tránh quá nhiệt/treo máy trên Windows Local.
- Làm sạch hoàn toàn artifact ASR ([Music], [Applause], ...).
- Chuẩn hóa transcript hỗ trợ Editor tìm kiếm linh hoạt (có dấu + không dấu).
"""

from __future__ import annotations

import gc
import re
import time
import json
import uuid
import urllib.request
import unicodedata
import os
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

import boto3
from ai_pipeline.config import config
from ai_pipeline.database.storage_client import StorageClientFactory
from utils.logger import log_exception, log_model_loading, logger


# =============================================================================
# Text Normalization Utilities
# =============================================================================

class VietnameseTextNormalizer:
    """
    Chuẩn hóa text phục vụ semantic indexing cho editor:
    - giữ text gốc có dấu
    - sinh normalized_text không dấu
    - sinh searchable_text = có dấu + không dấu + cụm rút gọn
    """

    NOISE_PATTERNS = [
        r"\[.*?\]",          # [Music], [Applause], ...
        r"\(.*?\)",          # (inaudible), ...
        r"<.*?>",            # <noise>
    ]

    FILLER_WORDS = {
        "à", "ờ", "ừ", "ơ", "ừm", "um", "uh", "ờm",
        "kiểu", "kiểu như", "thì", "nha", "nhé", "ha", "á", "ạ",
    }

    STOP_WORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
        "for", "of", "with", "by", "from", "as", "is", "was", "are",
        "were", "be", "have", "has", "had", "this", "that", "these",
        "those", "you", "your", "they", "their", "he", "she", "his", "her",
        "là", "và", "của", "có", "được", "trong", "một", "những", "các",
        "cho", "không", "đang", "này", "đó", "với", "về", "trên", "dưới",
        "tại", "thì", "lại", "cũng", "đã", "sẽ", "vừa", "bị", "do", "ở",
        "người", "tôi", "bạn", "anh", "chị", "em", "ông", "bà",
    }

    @classmethod
    def clean_whisper_text(cls, text: str) -> str:
        if not text:
            return ""

        cleaned = text
        for pattern in cls.NOISE_PATTERNS:
            cleaned = re.sub(pattern, " ", cleaned)

        cleaned = unicodedata.normalize("NFC", cleaned)
        cleaned = cleaned.replace("\n", " ").replace("\t", " ")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        cleaned = re.sub(r"\s+([,.;!?])", r"\1", cleaned)

        return cleaned

    @staticmethod
    def remove_diacritics(text: str) -> str:
        if not text:
            return ""

        text = text.replace("đ", "d").replace("Đ", "D")
        normalized = unicodedata.normalize("NFD", text)
        without_diacritics = "".join(
            ch for ch in normalized if unicodedata.category(ch) != "Mn"
        )
        return unicodedata.normalize("NFC", without_diacritics)

    @classmethod
    def normalize_for_index(cls, text: str) -> str:
        if not text:
            return ""

        text = cls.clean_whisper_text(text).lower()
        text = cls.remove_diacritics(text)
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @classmethod
    def normalize_preserve_vietnamese(cls, text: str) -> str:
        if not text:
            return ""

        text = cls.clean_whisper_text(text).lower()
        text = re.sub(r"[^\w\sÀ-ỹà-ỹĐđ]", " ", text, flags=re.UNICODE)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @classmethod
    def build_searchable_text(cls, text: str) -> str:
        if not text:
            return ""

        vi_text = cls.normalize_preserve_vietnamese(text)
        ascii_text = cls.normalize_for_index(text)

        if not vi_text and not ascii_text:
            return ""
        if vi_text == ascii_text:
            return vi_text

        return f"{vi_text} {ascii_text}".strip()

    @classmethod
    def tokenize_for_keywords(cls, text: str) -> List[str]:
        if not text:
            return []

        text = cls.normalize_preserve_vietnamese(text)
        tokens = []
        for token in text.split():
            token = token.strip(".,!?;:\"'()[]{}")
            if not token or len(token) <= 2:
                continue
            if token in cls.STOP_WORDS or token in cls.FILLER_WORDS:
                continue
            tokens.append(token)
        return tokens


# =============================================================================
# ASR Provider Base Interface
# =============================================================================

class ASRProvider(ABC):
    """Giao diện chung cho các mô hình nhận diện giọng nói (Local Whisper / AWS Transcribe)"""

    @abstractmethod
    def transcribe(self, audio_path: Path, language: str = None, **kwargs) -> Dict[str, Any]:
        """Thực hiện bóc băng audio"""
        pass

    def unload(self):
        """Giải phóng bộ nhớ (dùng cho local)"""
        pass

    def _get_empty_transcript(self) -> Dict[str, Any]:
        return {
            "segments": [], "words": [], "text": "",
            "normalized_text": "", "searchable_text": "", "language": "unknown",
        }

    def get_scene_transcript(
        self, transcript_data: Dict[str, Any], start_time: float, end_time: float, max_chars: int = 320,
    ) -> Dict[str, str]:
        raw_text = self.get_transcript_at_time(transcript_data, start_time, end_time)
        if max_chars > 0 and len(raw_text) > max_chars:
            raw_text = raw_text[:max_chars].rsplit(" ", 1)[0].strip()

        return {
            "raw_text": raw_text,
            "normalized_text": VietnameseTextNormalizer.normalize_for_index(raw_text),
            "searchable_text": VietnameseTextNormalizer.build_searchable_text(raw_text),
        }

    def get_transcript_at_time(self, transcript_data: Dict[str, Any], start_time: float, end_time: float) -> str:
        collected_segments: List[str] = []

        for seg in transcript_data.get("segments", []):
            seg_start = float(seg.get("start", 0.0))
            seg_end = float(seg.get("end", 0.0))
            if seg_end >= start_time and seg_start <= end_time:
                text = (seg.get("text") or "").strip()
                if text:
                    collected_segments.append(text)

        if collected_segments:
            return " ".join(collected_segments).strip()

        words = []
        for word in transcript_data.get("words", []):
            w_start = float(word.get("start", 0.0))
            w_end = float(word.get("end", 0.0))
            if w_end >= start_time and w_start <= end_time:
                w = (word.get("word") or "").strip()
                if w:
                    words.append(w)

        return " ".join(words).strip()

    def search_transcript(self, transcript_data: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        if not query:
            return []

        q_vi = VietnameseTextNormalizer.normalize_preserve_vietnamese(query)
        q_ascii = VietnameseTextNormalizer.normalize_for_index(query)

        matches = []
        for seg in transcript_data.get("segments", []):
            seg_text = seg.get("text", "")
            seg_norm = seg.get("normalized_text", "")
            seg_search = seg.get("searchable_text", "")

            haystack = " ".join([seg_text, seg_norm, seg_search]).lower()
            if (q_vi and q_vi in haystack) or (q_ascii and q_ascii in haystack):
                matches.append({
                    "start": seg.get("start", 0.0),
                    "end": seg.get("end", 0.0),
                    "text": seg_text,
                    "normalized_text": seg_norm,
                    "searchable_text": seg_search,
                    "match_query": query,
                })

        return matches


# =============================================================================
# Whisper ASR Model (Local)
# =============================================================================

class WhisperModel(ASRProvider):
    """Faster-Whisper ASR Model - Được tinh chỉnh nhẹ cho chip i7 Laptop."""

    def __init__(self, model_size: str = None):
        self.model_size = model_size or getattr(config.model, "whisper_model", "base")
        self.model = None
        self._load_model()

    def _load_model(self):
        """Khởi tạo mô hình định dạng nén INT8, giới hạn 4 luồng xử lý."""
        try:
            import faster_whisper  # lazy import

            log_model_loading(f"Faster-Whisper-{self.model_size}", "loading")

            model_cache_dir = (
                Path("/app/models/whisper")
                if Path("/app").exists()
                else Path("./models/whisper")
            )
            model_cache_dir.mkdir(parents=True, exist_ok=True)

            # Khống chế tài nguyên tối ưu cho i7-10700H
            self.model = faster_whisper.WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",    # Sử dụng lượng tử hóa int8 giảm tải CPU
                cpu_threads=4,          # Giới hạn 4 luồng (tránh ăn 100% CPU gây nóng máy)
                num_workers=1,          # Giảm worker xuống 1 để luồng I/O mượt mà
                download_root=str(model_cache_dir),
            )

            log_model_loading(f"Faster-Whisper-{self.model_size}", "loaded")
            logger.info(f" Faster-Whisper '{self.model_size}' sẵn sàng ")

        except Exception as e:
            log_exception(e, "WhisperModel._load_model")
            raise

    def transcribe(
        self,
        audio_path: Path,
        language: str = None,
        word_timestamps: bool = True,
        beam_size: int = 3,       # Giảm từ 5 xuống 3 để xử lý nhanh hơn, chất lượng ít đổi
        vad_filter: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        try:
            start_time = time.time()
            logger.info(f"[Whisper] Đang xử lý âm thanh: {audio_path.name}")

            segments_generator, info = self.model.transcribe(
                str(audio_path),
                language=language,
                word_timestamps=word_timestamps,
                beam_size=beam_size,
                vad_filter=vad_filter,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    max_speech_duration_s=30,
                ),
                temperature=0.0,
            )

            detected_lang = getattr(info, "language", "unknown")
            logger.info(f"Ngôn ngữ phát hiện: {detected_lang}")

            segments = list(segments_generator)
            transcript_data = self._format_transcript(segments, detected_lang)

            duration = time.time() - start_time
            logger.info(f"[Whisper] Xử lý hoàn tất sau {duration:.2f}s | {len(transcript_data['segments'])} segments")

            return transcript_data

        except Exception as e:
            log_exception(e, "WhisperModel.transcribe")
            return self._get_empty_transcript()
        finally:
            gc.collect()  # Tự động dọn RAM rác sau mỗi lượt nhận diện xong

    def _format_transcript(self, segments, language: str) -> Dict[str, Any]:
        formatted_segments: List[Dict[str, Any]] = []
        all_words: List[Dict[str, Any]] = []

        for segment in segments:
            raw_text = (segment.text or "").strip()
            clean_text = VietnameseTextNormalizer.clean_whisper_text(raw_text)

            if not clean_text:
                continue

            seg_words: List[Dict[str, Any]] = []
            if hasattr(segment, "words") and segment.words:
                for word in segment.words:
                    word_str = (getattr(word, "word", "") or "").strip()
                    word_str = VietnameseTextNormalizer.clean_whisper_text(word_str)

                    if not word_str or word_str.startswith("[") or word_str.startswith("("):
                        continue

                    word_data = {
                        "word": word_str,
                        "start": float(getattr(word, "start", 0.0)),
                        "end": float(getattr(word, "end", 0.0)),
                        "score": float(getattr(word, "probability", 1.0)),
                    }
                    seg_words.append(word_data)
                    all_words.append(word_data)

            seg_data = {
                "start": float(getattr(segment, "start", 0.0)),
                "end": float(getattr(segment, "end", 0.0)),
                "text": clean_text,
                "normalized_text": VietnameseTextNormalizer.normalize_for_index(clean_text),
                "searchable_text": VietnameseTextNormalizer.build_searchable_text(clean_text),
                "words": seg_words,
            }
            formatted_segments.append(seg_data)

        full_text = " ".join(seg["text"] for seg in formatted_segments).strip()
        normalized_text = VietnameseTextNormalizer.normalize_for_index(full_text)
        searchable_text = VietnameseTextNormalizer.build_searchable_text(full_text)

        return {
            "segments": formatted_segments,
            "words": all_words,
            "text": full_text,
            "normalized_text": normalized_text,
            "searchable_text": searchable_text,
            "language": language or "unknown",
        }

    def unload(self):
        """Giải phóng hoàn toàn mô hình khỏi RAM và dọn bộ nhớ hệ thống."""
        if self.model is not None:
            try:
                del self.model
            except Exception:
                pass
            self.model = None
        gc.collect()
        logger.info(f"Faster-Whisper model '{self.model_size}' giải phóng bộ nhớ thành công.")


# =============================================================================
# AWS Transcribe Model (Cloud)
# =============================================================================

class AWSTranscribeProvider(ASRProvider):
    """Sử dụng Amazon Transcribe chuẩn kiến trúc AWS Serverless"""

    def __init__(self):
        self.s3_client = StorageClientFactory.from_env()
        # S3 bucket configuration comes from the env var already setup in storage_client.py
        # But we need it to construct S3 URI for Amazon Transcribe
        self.bucket = os.environ.get("AWS_S3_BUCKET", "cloudforge-media-upload")
        self.transcribe_client = boto3.client(
            "transcribe",
            region_name=os.getenv("AWS_DEFAULT_REGION", "ap-southeast-1")
        )
        logger.info(" AWS Transcribe Provider sẵn sàng ")

    def transcribe(self, audio_path: Path, language: str = None, **kwargs) -> Dict[str, Any]:
        try:
            start_time = time.time()
            logger.info(f"[AWSTranscribe] Đang xử lý: {audio_path.name}")

            job_id = uuid.uuid4().hex
            remote_path = f"audio-temp/{job_id}_{audio_path.name}"

            # 1. Upload audio to S3 (Trạm trung chuyển)
            logger.info(f"[AWSTranscribe] Tải âm thanh lên s3://{self.bucket}/{remote_path}")
            if not self.s3_client.upload_file(str(audio_path), remote_path):
                raise Exception("Không thể upload audio lên S3 cho quá trình Transcribe")

            job_uri = f"s3://{self.bucket}/{remote_path}"
            job_name = f"sma-transcribe-{job_id}"

            # 2. Start Transcription Job
            logger.info(f"[AWSTranscribe] Khởi tạo Job: {job_name}")
            params = {
                "TranscriptionJobName": job_name,
                "Media": {"MediaFileUri": job_uri},
            }
            if language:
                params["LanguageCode"] = language
            else:
                params["IdentifyLanguage"] = True

            self.transcribe_client.start_transcription_job(**params)

            # 3. Polling for completion
            while True:
                res = self.transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
                status = res["TranscriptionJob"]["TranscriptionJobStatus"]
                if status in ["COMPLETED", "FAILED"]:
                    break
                logger.info(f"[AWSTranscribe] Job Status: {status}. Đợi 5s...")
                time.sleep(5)

            if status == "FAILED":
                err = res["TranscriptionJob"].get("FailureReason", "Unknown Error")
                raise Exception(f"Transcribe job {job_name} thất bại: {err}")

            # 4. Download and parse results
            logger.info(f"[AWSTranscribe] Job hoàn tất. Đang parse JSON từ AWS...")
            transcript_uri = res["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]

            detected_lang = res["TranscriptionJob"].get("LanguageCode", language or "unknown")

            req = urllib.request.Request(transcript_uri)
            with urllib.request.urlopen(req) as response:
                transcript_json = json.loads(response.read().decode("utf-8"))

            result = self._parse_aws_json(transcript_json, detected_lang)

            # 5. Cleanup S3 temp audio file
            logger.info(f"[AWSTranscribe] Dọn dẹp file tạm trên S3: {remote_path}")
            self.s3_client.delete_file(remote_path)

            logger.info(f"[AWSTranscribe] Xử lý hoàn tất sau {time.time()-start_time:.2f}s")
            return result

        except Exception as e:
            log_exception(e, "AWSTranscribeProvider.transcribe")
            return self._get_empty_transcript()

    def _parse_aws_json(self, data: dict, language: str) -> Dict[str, Any]:
        """Convert format JSON của AWS Transcribe về chuẩn dict của Whisper để tương thích Editor."""
        items = data.get("results", {}).get("items", [])
        transcripts = data.get("results", {}).get("transcripts", [])
        full_text = transcripts[0].get("transcript", "") if transcripts else ""

        formatted_segments = []
        all_words = []

        current_segment_words = []
        current_segment_text = []
        current_start = 0.0

        for item in items:
            item_type = item.get("type")
            if item_type == "pronunciation":
                word_str = item["alternatives"][0]["content"]
                start = float(item.get("start_time", 0.0))
                end = float(item.get("end_time", 0.0))
                score = float(item["alternatives"][0].get("confidence", 1.0))

                clean_word = VietnameseTextNormalizer.clean_whisper_text(word_str)
                if not current_segment_words:
                    current_start = start

                word_data = {"word": clean_word, "start": start, "end": end, "score": score}
                current_segment_words.append(word_data)
                all_words.append(word_data)
                current_segment_text.append(word_str)

            elif item_type == "punctuation":
                punct_str = item["alternatives"][0]["content"]
                if current_segment_text:
                    current_segment_text[-1] += punct_str

                # Ngắt segment ở dấu câu
                if punct_str in [".", "?", "!"] and current_segment_words:
                    seg_text = " ".join(current_segment_text)
                    clean_text = VietnameseTextNormalizer.clean_whisper_text(seg_text)
                    formatted_segments.append({
                        "start": current_start,
                        "end": current_segment_words[-1]["end"],
                        "text": clean_text,
                        "normalized_text": VietnameseTextNormalizer.normalize_for_index(clean_text),
                        "searchable_text": VietnameseTextNormalizer.build_searchable_text(clean_text),
                        "words": current_segment_words
                    })
                    current_segment_words = []
                    current_segment_text = []

        # Thêm segment cuối nếu còn sót
        if current_segment_words:
            seg_text = " ".join(current_segment_text)
            clean_text = VietnameseTextNormalizer.clean_whisper_text(seg_text)
            formatted_segments.append({
                "start": current_start,
                "end": current_segment_words[-1]["end"],
                "text": clean_text,
                "normalized_text": VietnameseTextNormalizer.normalize_for_index(clean_text),
                "searchable_text": VietnameseTextNormalizer.build_searchable_text(clean_text),
                "words": current_segment_words
            })

        return {
            "segments": formatted_segments,
            "words": all_words,
            "text": VietnameseTextNormalizer.clean_whisper_text(full_text),
            "normalized_text": VietnameseTextNormalizer.normalize_for_index(full_text),
            "searchable_text": VietnameseTextNormalizer.build_searchable_text(full_text),
            "language": language
        }


# =============================================================================
# Transcript Processor Utilities
# =============================================================================

class TranscriptProcessor:
    """Helper utilities cho semantic indexer / editor retrieval."""

    @staticmethod
    def merge_short_segments(segments: List[Dict[str, Any]], min_duration: float = 2.0) -> List[Dict[str, Any]]:
        if not segments:
            return []

        merged: List[Dict[str, Any]] = []
        current = dict(segments[0])
        current.setdefault("words", [])

        for seg in segments[1:]:
            cur_duration = float(current.get("end", 0.0)) - float(current.get("start", 0.0))
            if cur_duration < min_duration:
                current["end"] = seg.get("end", current["end"])
                current["text"] = f"{current.get('text', '').strip()} {seg.get('text', '').strip()}".strip()
                current["words"] = (current.get("words", []) or []) + (seg.get("words", []) or [])
            else:
                TranscriptProcessor._refresh_segment_index_fields(current)
                merged.append(current)
                current = dict(seg)
                current.setdefault("words", [])

        TranscriptProcessor._refresh_segment_index_fields(current)
        merged.append(current)
        return merged

    @staticmethod
    def _refresh_segment_index_fields(segment: Dict[str, Any]) -> None:
        text = segment.get("text", "") or ""
        segment["normalized_text"] = VietnameseTextNormalizer.normalize_for_index(text)
        segment["searchable_text"] = VietnameseTextNormalizer.build_searchable_text(text)

    @staticmethod
    def extract_keywords(text: str, top_n: int = 15) -> List[str]:
        if not text:
            return []
        tokens = VietnameseTextNormalizer.tokenize_for_keywords(text)
        if not tokens:
            return []
        freq = Counter(tokens)
        return [word for word, _ in freq.most_common(top_n)]

    @staticmethod
    def extract_editor_keywords(caption: str, transcript_snippet: str = "", top_n: int = 12) -> List[str]:
        source = f"{(caption or '').strip()} {(transcript_snippet or '').strip()}".strip()
        if not source:
            return []

        tokens = VietnameseTextNormalizer.tokenize_for_keywords(source)
        if not tokens:
            return []

        caption_tokens = VietnameseTextNormalizer.tokenize_for_keywords(caption or "")
        weighted_tokens = tokens + caption_tokens

        freq = Counter(weighted_tokens)
        ranked = [word for word, _ in freq.most_common(top_n)]

        seen = set()
        result = []
        for kw in ranked:
            if kw not in seen:
                seen.add(kw)
                result.append(kw)
        return result[:top_n]

    @staticmethod
    def build_scene_search_text(caption: str, transcript_snippet: str = "", tags: Optional[List[str]] = None) -> str:
        parts = []
        if caption: parts.append(caption.strip())
        if transcript_snippet: parts.append(transcript_snippet.strip())
        if tags: parts.append(" ".join(t.strip() for t in tags if t and t.strip()))

        raw = " ".join(parts).strip()
        return VietnameseTextNormalizer.build_searchable_text(raw)

    @staticmethod
    def build_scene_embedding_text(caption: str, transcript_snippet: str = "", tags: Optional[List[str]] = None) -> str:
        parts = []
        if caption: parts.append(caption.strip())
        if transcript_snippet: parts.append(transcript_snippet.strip())
        if tags:
            tag_line = " ".join(t.strip() for t in tags if t and t.strip())
            if tag_line: parts.append(tag_line)

        raw = "\n".join(p for p in parts if p).strip()
        search_text = VietnameseTextNormalizer.build_searchable_text(raw)

        if search_text and search_text != raw:
            return f"{raw}\n{search_text}".strip()
        return raw


# =============================================================================
# Factory
# =============================================================================

def create_asr_model() -> ASRProvider:
    provider = getattr(config.model, "asr_provider", "aws")
    if provider == "aws":
        return AWSTranscribeProvider()
    return WhisperModel()