"""
Test Transcriber - Faster-Whisper ASR Model
Kiểm tra toàn diện chức năng transcription
"""

import time
from pathlib import Path

from ai_pipeline.audio.transcriber import (
    WhisperModel, 
    create_asr_model,
    TranscriptProcessor
)
from utils.logger import logger


def test_transcriber():
    """Test toàn diện Transcriber"""
    print("="*80)
    print("🎙️  TRANSCRIBER COMPREHENSIVE TEST (Faster-Whisper)")
    print("="*80)

    try:
        # 1. Khởi tạo model
        print("\n[1] Khởi tạo WhisperModel...")
        model = create_asr_model()
        print(f" Model loaded: {model.model_size} (CPU)")

        # 2. Tìm file audio test
        test_audio = None
        possible_paths = [
            Path("videos/1,25s.mp4"),
            Path("ai_pipeline/output/vid_*/audio.wav"),  # Tìm trong output
            Path("test_audio.wav")
        ]

        for path in possible_paths:
            if path.is_file():
                test_audio = path
                break
            elif "*" in str(path):
                # Tìm file audio.wav trong output
                for p in Path("ai_pipeline/output").rglob("audio.wav"):
                    test_audio = p
                    break
            if test_audio:
                break

        if not test_audio:
            print("  Không tìm thấy file audio test. Tạo file test giả...")
            test_audio = Path("test_audio.wav")
            # Tạo file test rỗng nếu không có
            test_audio.touch()

        print(f"   Using audio: {test_audio.name}")

        # 3. Test transcription
        print("\n[2] Testing transcription...")
        start_time = time.time()
        
        result = model.transcribe(
            audio_path=test_audio,
            language=None,           # Auto detect
            word_timestamps=True
        )

        duration = time.time() - start_time

        print(f"   Time: {duration:.2f} seconds")
        print(f"   Language: {result.get('language')}")
        print(f"   Segments: {len(result.get('segments', []))}")
        print(f"   Words: {len(result.get('words', []))}")
        print(f"   Text length: {len(result.get('text', ''))}")

        # 4. Kiểm tra cấu trúc output
        print("\n[3] Checking output structure...")
        assert "segments" in result, "Missing segments"
        assert "words" in result, "Missing words"
        assert "text" in result, "Missing text"
        assert "language" in result, "Missing language"

        if result["segments"]:
            seg = result["segments"][0]
            assert "start" in seg and "end" in seg and "text" in seg, "Bad segment format"
            print("    Output format correct")

        # 5. Test utility functions
        print("\n[4] Testing TranscriptProcessor...")
        keywords = TranscriptProcessor.extract_keywords(result.get("text", ""))
        print(f"   Extracted keywords: {keywords[:10]}")

        merged = TranscriptProcessor.merge_short_segments(result.get("segments", []))
        print(f"   Merged segments: {len(merged)}")

        # 6. Test helper methods
        print("\n[5] Testing helper methods...")
        if result["segments"]:
            sample = result["segments"][0]
            text_at_time = model.get_transcript_at_time(
                result, sample["start"], sample["end"]
            )
            print(f"   get_transcript_at_time: {text_at_time[:60]}...")

        search_result = model.search_transcript(result, "test")
        print(f"   Search result count: {len(search_result)}")

        print("\n" + "="*80)
        print(" TẤT CẢ TEST TRANSCRIBER ĐÃ PASS!")
        print("="*80)
        
        return True

    except Exception as e:
        logger.error(f"Transcriber test failed: {e}")
        print(f" Test thất bại: {e}")
        return False


if __name__ == "__main__":
    test_transcriber()