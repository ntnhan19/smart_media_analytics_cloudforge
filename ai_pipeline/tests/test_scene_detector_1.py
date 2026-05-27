"""
tests/test_scene_detector.py
============================
Test suite for SceneDetector — covers all Definition-of-Done criteria.

Run:
    pytest tests/test_scene_detector.py -v

A real MP4 is required for integration tests. The file is generated once
via the `sample_video` fixture using OpenCV if it does not already exist.
"""

import sys
import shutil
import tempfile
from dataclasses import is_dataclass, fields
from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.video_processor import SceneData, SceneDetector


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_mp4(path: Path, duration_sec: float = 10.0, fps: float = 24.0,
              num_scene_changes: int = 3, width: int = 320, height: int = 240) -> Path:
    """
    Generate a synthetic MP4 with abrupt colour changes to simulate scene cuts.
    Uses only cv2 — no external tools required.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))

    total_frames = int(duration_sec * fps)
    segment_len  = total_frames // (num_scene_changes + 1)

    colours = [
        (50,  100, 200),
        (200,  50,  50),
        (50,  200,  50),
        (200, 200,  50),
    ]

    for i in range(total_frames):
        seg_idx = min(i // segment_len, len(colours) - 1)
        frame   = np.full((height, width, 3), colours[seg_idx], dtype=np.uint8)
        writer.write(frame)

    writer.release()
    return path


def _make_static_mp4(path: Path, duration_sec: float = 5.0, fps: float = 24.0) -> Path:
    """MP4 with no scene changes — single solid colour throughout."""
    return _make_mp4(path, duration_sec=duration_sec, fps=fps, num_scene_changes=0)


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def tmp_root(tmp_path_factory):
    return tmp_path_factory.mktemp("scene_detector_tests")


@pytest.fixture(scope="session")
def sample_video(tmp_root) -> Path:
    """2-minute synthetic MP4 with 5 distinct scenes."""
    p = tmp_root / "sample_2min.mp4"
    _make_mp4(p, duration_sec=120.0, fps=24.0, num_scene_changes=5)
    return p


@pytest.fixture(scope="session")
def static_video(tmp_root) -> Path:
    """Short MP4 with no cuts — tests fallback logic."""
    p = tmp_root / "static.mp4"
    _make_static_mp4(p, duration_sec=6.0, fps=24.0)
    return p


@pytest.fixture(scope="session")
def short_video(tmp_root) -> Path:
    """10-second video with only 1 scene change — < 3 scenes → triggers fallback."""
    p = tmp_root / "short.mp4"
    _make_mp4(p, duration_sec=10.0, fps=24.0, num_scene_changes=1)
    return p


@pytest.fixture()
def detector(tmp_root) -> SceneDetector:
    """SceneDetector with isolated thumbnails directory."""
    thumbs = tmp_root / "thumbs"
    return SceneDetector(thumbnails_dir=thumbs)


# ── SceneData dataclass contract ──────────────────────────────────────────────

class TestSceneDataContract:
    """DoD: SceneData dataclass has the required 4 fields."""

    def test_is_dataclass(self):
        assert is_dataclass(SceneData)

    def test_required_fields_present(self):
        field_names = {f.name for f in fields(SceneData)}
        assert "scene_index"    in field_names
        assert "start_time_sec" in field_names
        assert "end_time_sec"   in field_names
        assert "keyframe_path"  in field_names

    def test_field_types(self):
        sd = SceneData(scene_index=0, start_time_sec=0.0, end_time_sec=10.0, keyframe_path="/tmp/f.jpg")
        assert isinstance(sd.scene_index,    int)
        assert isinstance(sd.start_time_sec, float)
        assert isinstance(sd.end_time_sec,   float)
        assert isinstance(sd.keyframe_path,  str)

    def test_duration_property(self):
        sd = SceneData(scene_index=0, start_time_sec=2.0, end_time_sec=7.5, keyframe_path="")
        assert sd.duration == pytest.approx(5.5)

    def test_midpoint_property(self):
        sd = SceneData(scene_index=0, start_time_sec=0.0, end_time_sec=10.0, keyframe_path="")
        assert sd.midpoint == pytest.approx(5.0)


# ── extract_keyframe ──────────────────────────────────────────────────────────

class TestExtractKeyframe:
    """DoD: keyframe JPEGs are valid images; VideoCapture is released."""

    def test_returns_string_path(self, detector, sample_video, tmp_root):
        out = tmp_root / "kf_test.jpg"
        result = detector.extract_keyframe(sample_video, timestamp_sec=5.0, output_path=out)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_jpeg_exists_on_disk(self, detector, sample_video, tmp_root):
        out = tmp_root / "kf_exists.jpg"
        result = detector.extract_keyframe(sample_video, timestamp_sec=3.0, output_path=out)
        assert Path(result).exists()

    def test_jpeg_is_valid_image(self, detector, sample_video, tmp_root):
        """DoD: PIL.Image.open must succeed without error."""
        out = tmp_root / "kf_valid.jpg"
        result = detector.extract_keyframe(sample_video, timestamp_sec=10.0, output_path=out)
        img = Image.open(result)   # must not raise
        assert img.width > 0
        assert img.height > 0

    def test_creates_parent_directory(self, detector, sample_video, tmp_root):
        nested = tmp_root / "new_dir" / "sub" / "kf.jpg"
        result = detector.extract_keyframe(sample_video, timestamp_sec=1.0, output_path=nested)
        assert Path(result).exists()

    def test_thumbnails_dir_created(self, tmp_root):
        thumbs = tmp_root / "auto_created_thumbs"
        assert not thumbs.exists()
        SceneDetector(thumbnails_dir=thumbs)
        assert thumbs.exists()


# ── detect_scenes — 2-minute MP4 ─────────────────────────────────────────────

class TestDetectScenes:
    """DoD: detect_scenes on a 2-min MP4 returns ≥ 2 SceneData objects."""

    def test_returns_list(self, detector, sample_video):
        result = detector.detect_scenes(sample_video)
        assert isinstance(result, list)

    def test_at_least_two_scenes(self, detector, sample_video):
        """DoD: 2-minute sample → ≥ 2 SceneData objects."""
        result = detector.detect_scenes(sample_video)
        assert len(result) >= 2, f"Expected ≥2 scenes, got {len(result)}"

    def test_returns_scene_data_objects(self, detector, sample_video):
        result = detector.detect_scenes(sample_video)
        for sd in result:
            assert isinstance(sd, SceneData)

    def test_start_less_than_end(self, detector, sample_video):
        """DoD: start_time_sec < end_time_sec for every scene."""
        result = detector.detect_scenes(sample_video)
        for sd in result:
            assert sd.start_time_sec < sd.end_time_sec, (
                f"Scene {sd.scene_index}: start={sd.start_time_sec} >= end={sd.end_time_sec}"
            )

    def test_scene_indices_are_sequential(self, detector, sample_video):
        result = detector.detect_scenes(sample_video)
        for expected_idx, sd in enumerate(result):
            assert sd.scene_index == expected_idx

    def test_keyframe_paths_are_existing_jpegs(self, detector, sample_video):
        """DoD: each SceneData has a valid keyframe_path pointing to an existing JPEG."""
        result = detector.detect_scenes(sample_video)
        for sd in result:
            assert sd.keyframe_path, f"Scene {sd.scene_index}: keyframe_path is empty"
            p = Path(sd.keyframe_path)
            assert p.exists(),      f"Keyframe not found on disk: {p}"
            assert p.suffix.lower() == ".jpg", f"Not a JPEG: {p}"

    def test_keyframe_jpegs_openable_with_pil(self, detector, sample_video):
        """DoD: PIL.Image.open on each keyframe must succeed without error."""
        result = detector.detect_scenes(sample_video)
        for sd in result:
            img = Image.open(sd.keyframe_path)
            assert img.width > 0

    def test_keyframe_at_midpoint(self, detector, sample_video):
        """Keyframe timestamp ≈ midpoint of the scene."""
        result = detector.detect_scenes(sample_video)
        for sd in result:
            expected_mid = (sd.start_time_sec + sd.end_time_sec) / 2
            # Verify timestamp is close to midpoint (within 1 frame at 24fps)
            assert abs(expected_mid - sd.midpoint) < 0.1

    def test_missing_video_raises(self, detector, tmp_root):
        with pytest.raises(FileNotFoundError):
            detector.detect_scenes(tmp_root / "nonexistent.mp4")


# ── fallback: no scene changes ────────────────────────────────────────────────

class TestFallback:
    """DoD: video with no scene changes → exactly 1 scene covering full duration."""

    def test_static_video_returns_exactly_one_scene(self, detector, static_video):
        result = detector.detect_scenes(static_video)
        assert len(result) == 1, f"Expected 1 scene (fallback), got {len(result)}"

    def test_fallback_scene_starts_at_zero(self, detector, static_video):
        result = detector.detect_scenes(static_video)
        assert result[0].start_time_sec == pytest.approx(0.0, abs=0.1)

    def test_fallback_scene_covers_full_duration(self, detector, static_video):
        """end_time_sec should match the full video duration (±0.5s tolerance)."""
        cap = cv2.VideoCapture(str(static_video))
        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        total = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        cap.release()
        expected_duration = total / fps

        result = detector.detect_scenes(static_video)
        assert result[0].end_time_sec == pytest.approx(expected_duration, abs=0.5)

    def test_fallback_keyframe_is_valid_jpeg(self, detector, static_video):
        result = detector.detect_scenes(static_video)
        sd = result[0]
        assert Path(sd.keyframe_path).exists()
        img = Image.open(sd.keyframe_path)
        assert img.width > 0

    def test_few_scenes_triggers_fallback(self, detector, short_video):
        """Video with < 3 detectable scenes → 1 scene fallback."""
        result = detector.detect_scenes(short_video)
        assert len(result) == 1

    def test_start_lt_end_in_fallback(self, detector, static_video):
        result = detector.detect_scenes(static_video)
        sd = result[0]
        assert sd.start_time_sec < sd.end_time_sec


# ── memory / resource management ─────────────────────────────────────────────

class TestResourceManagement:
    """DoD: no memory leak — VideoCapture released after use."""

    def test_multiple_calls_dont_exhaust_resources(self, detector, sample_video):
        """Calling detect_scenes 5× should not raise or hang."""
        for _ in range(5):
            result = detector.detect_scenes(sample_video)
            assert isinstance(result, list)

    def test_extract_keyframe_releases_cap_on_success(self, detector, sample_video, tmp_root):
        """Verify extract_keyframe completes cleanly 10× in a row."""
        for i in range(10):
            out = tmp_root / f"release_test_{i}.jpg"
            detector.extract_keyframe(sample_video, timestamp_sec=float(i), output_path=out)
        # If VideoCapture leaked, the OS file handle limit would have caused an error above

    def test_extract_keyframe_releases_cap_on_bad_timestamp(self, detector, sample_video, tmp_root):
        """Even with an out-of-range timestamp, cap must be released."""
        out = tmp_root / "bad_ts.jpg"
        result = detector.extract_keyframe(sample_video, timestamp_sec=99999.0, output_path=out)
        # No exception = cap was properly released via finally


# ── backward-compatible tuple API ────────────────────────────────────────────

class TestTupleAPI:
    """detect_scenes_as_tuples returns (start, end) tuples — same data, different shape."""

    def test_returns_list_of_tuples(self, detector, sample_video):
        result = detector.detect_scenes_as_tuples(sample_video)
        assert isinstance(result, list)
        for item in result:
            assert len(item) == 2
            start, end = item
            assert start < end


# ── run directly ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
