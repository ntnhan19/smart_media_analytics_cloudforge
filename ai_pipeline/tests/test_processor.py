"""
Unit Tests — VideoProcessor JSON output + ECS Entrypoint pipeline

Đảm bảo:
  1. VideoProcessor.create_proxy() → đúng FFmpeg command, trả về bool
  2. SceneDetector.detect_scenes() → trả về List[SceneData] đúng cấu trúc
  3. entrypoint.run_task() → output JSON đúng schema (asset_id, scenes[], status)
  4. entrypoint.TaskInput   → parse/validate input JSON
  5. entrypoint.step_*      → unit test từng bước pipeline

Run:
    pytest ai_pipeline/tests/test_processor.py -v
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call
from dataclasses import dataclass
from typing import List, Optional

import pytest

# ── Minimal stubs cho imports nặng (cv2, scenedetect, config) ─────────────────
# Phải stub trước khi import các module cần test
import types

# Stub cv2
cv2_stub = types.ModuleType("cv2")
cv2_stub.VideoCapture = MagicMock()
cv2_stub.CAP_PROP_FPS = 5
cv2_stub.CAP_PROP_POS_FRAMES = 1
cv2_stub.CAP_PROP_FRAME_COUNT = 7
cv2_stub.IMWRITE_JPEG_QUALITY = 1
cv2_stub.imwrite = MagicMock(return_value=True)
cv2_stub.COLOR_BGR2RGB = 4
cv2_stub.cvtColor = MagicMock(return_value=None)
sys.modules.setdefault("cv2", cv2_stub)

# Stub numpy
import numpy as np  # usually available; if not, stub it too

# Stub scenedetect
sd_stub = types.ModuleType("scenedetect")
sd_stub.open_video = MagicMock()
sd_stub.SceneManager = MagicMock()
sys.modules.setdefault("scenedetect", sd_stub)
det_stub = types.ModuleType("scenedetect.detectors")
det_stub.ContentDetector = MagicMock()
sys.modules.setdefault("scenedetect.detectors", det_stub)

# Stub utils.logger
logger_stub = types.ModuleType("utils")
logger_inner = types.ModuleType("utils.logger")
_mock_logger = MagicMock()
_mock_logger.info = MagicMock()
_mock_logger.debug = MagicMock()
_mock_logger.warning = MagicMock()
_mock_logger.error = MagicMock()
_mock_logger.success = MagicMock()
logger_inner.logger = _mock_logger
logger_inner.log_exception = MagicMock()
logger_inner.ProgressTracker = MagicMock()
sys.modules.setdefault("utils", logger_stub)
sys.modules.setdefault("utils.logger", logger_inner)

# Stub ai_pipeline.config
config_stub_mod = types.ModuleType("ai_pipeline.config")
_video_cfg = MagicMock()
_video_cfg.proxy_height = 480
_video_cfg.proxy_preset = "fast"
_video_cfg.proxy_crf = 28
_video_cfg.scene_threshold = 27.0
_video_cfg.min_scene_length = 2.0
_cfg = MagicMock()
_cfg.video = _video_cfg
_cfg.web.allowed_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
config_stub_mod.config = _cfg
config_stub_mod.THUMBNAILS_DIR = Path("/tmp/thumbnails")
sys.modules.setdefault("ai_pipeline.config", config_stub_mod)
sys.modules.setdefault("ai_pipeline", types.ModuleType("ai_pipeline"))

# Now safe to import the real modules
from ai_pipeline.scene_detection.scene_detector import (  # noqa: E402
    SceneData,
    VideoProcessor,
    SceneDetector,
)
from ai_pipeline.ecs.entrypoint import (  # noqa: E402
    TaskInput,
    TaskWorkspace,
    run_task,
    step_download,
    step_process,
    step_upload,
    step_build_output,
    _generate_asset_id,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_scene(idx: int, start: float, end: float, kf: str = "") -> SceneData:
    return SceneData(
        scene_index=idx,
        start_time_sec=start,
        end_time_sec=end,
        keyframe_path=kf,
    )


def _raw_input(**overrides) -> dict:
    base = {"bucket": "media", "video_s3_key": "uploads/beach.mp4"}
    base.update(overrides)
    return base


# ─────────────────────────────────────────────────────────────────────────────
# SceneData dataclass
# ─────────────────────────────────────────────────────────────────────────────

class TestSceneData:

    def test_duration_property(self):
        s = _make_scene(0, 2.0, 7.5)
        assert s.duration == pytest.approx(5.5)

    def test_midpoint_property(self):
        s = _make_scene(0, 4.0, 10.0)
        assert s.midpoint == pytest.approx(7.0)

    def test_zero_duration(self):
        s = _make_scene(0, 5.0, 5.0)
        assert s.duration == 0.0
        assert s.midpoint == 5.0


# ─────────────────────────────────────────────────────────────────────────────
# VideoProcessor.create_proxy
# ─────────────────────────────────────────────────────────────────────────────

class TestVideoProcessorCreateProxy:

    @pytest.fixture
    def processor(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="ffmpeg ok", stderr="")
            vp = VideoProcessor()
        return vp

    def test_create_proxy_returns_true_on_success(self, processor, tmp_path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            ok = processor.create_proxy(tmp_path / "input.mp4", tmp_path / "proxy.mp4")
        assert ok is True

    def test_create_proxy_returns_false_on_ffmpeg_error(self, processor, tmp_path):
        import subprocess
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "ffmpeg", stderr="error")
            ok = processor.create_proxy(tmp_path / "input.mp4", tmp_path / "proxy.mp4")
        assert ok is False

    def test_create_proxy_uses_correct_crf(self, processor, tmp_path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            processor.create_proxy(tmp_path / "input.mp4", tmp_path / "proxy.mp4")
            cmd = mock_run.call_args.args[0]
        assert "-crf" in cmd
        crf_idx = cmd.index("-crf")
        assert cmd[crf_idx + 1] == "28"

    def test_create_proxy_uses_correct_scale_filter(self, processor, tmp_path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            processor.create_proxy(tmp_path / "input.mp4", tmp_path / "proxy.mp4")
            cmd = mock_run.call_args.args[0]
        vf_idx = cmd.index("-vf")
        assert "480" in cmd[vf_idx + 1]

    def test_create_proxy_uses_libx264(self, processor, tmp_path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            processor.create_proxy(tmp_path / "input.mp4", tmp_path / "proxy.mp4")
            cmd = mock_run.call_args.args[0]
        assert "libx264" in cmd

    def test_create_proxy_creates_output_parent_dir(self, processor, tmp_path):
        deep = tmp_path / "a" / "b" / "proxy.mp4"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            processor.create_proxy(tmp_path / "input.mp4", deep)
        assert deep.parent.exists()


# ─────────────────────────────────────────────────────────────────────────────
# SceneDetector.detect_scenes → JSON-ready output
# ─────────────────────────────────────────────────────────────────────────────

class TestSceneDetectorOutput:

    def _make_detector(self, tmp_path) -> SceneDetector:
        d = SceneDetector.__new__(SceneDetector)
        d.threshold = 27.0
        d.min_scene_length = 2.0
        d.thumbnails_dir = tmp_path / "thumbs"
        d.thumbnails_dir.mkdir(parents=True, exist_ok=True)
        return d

    def test_detect_scenes_returns_list_of_scene_data(self, tmp_path):
        detector = self._make_detector(tmp_path)
        fake_video = tmp_path / "video.mp4"
        fake_video.write_bytes(b"fake")

        raw_scenes = [(0.0, 5.0), (5.0, 12.3), (12.3, 20.0)]
        with patch.object(detector, "_run_scene_detection", return_value=raw_scenes), \
             patch.object(detector, "extract_keyframe", return_value="/tmp/kf.jpg"):
            result = detector.detect_scenes(fake_video)

        assert isinstance(result, list)
        assert all(isinstance(s, SceneData) for s in result)

    def test_detect_scenes_correct_count(self, tmp_path):
        detector = self._make_detector(tmp_path)
        fake_video = tmp_path / "video.mp4"
        fake_video.write_bytes(b"fake")

        raw_scenes = [(0.0, 3.0), (3.0, 8.5), (8.5, 15.0), (15.0, 21.0)]
        with patch.object(detector, "_run_scene_detection", return_value=raw_scenes), \
             patch.object(detector, "extract_keyframe", return_value=""):
            result = detector.detect_scenes(fake_video)

        assert len(result) == 4

    def test_detect_scenes_indices_sequential(self, tmp_path):
        detector = self._make_detector(tmp_path)
        fake_video = tmp_path / "video.mp4"
        fake_video.write_bytes(b"fake")

        raw_scenes = [(0.0, 5.0), (5.0, 10.0), (10.0, 15.0)]
        with patch.object(detector, "_run_scene_detection", return_value=raw_scenes), \
             patch.object(detector, "extract_keyframe", return_value=""):
            result = detector.detect_scenes(fake_video)

        assert [s.scene_index for s in result] == [0, 1, 2]

    def test_detect_scenes_timestamps_preserved(self, tmp_path):
        detector = self._make_detector(tmp_path)
        fake_video = tmp_path / "video.mp4"
        fake_video.write_bytes(b"fake")

        raw_scenes = [(1.5, 6.0), (6.0, 12.2), (12.2, 19.9)]
        with patch.object(detector, "_run_scene_detection", return_value=raw_scenes), \
             patch.object(detector, "extract_keyframe", return_value=""):
            result = detector.detect_scenes(fake_video)

        assert result[0].start_time_sec == pytest.approx(1.5)
        assert result[0].end_time_sec   == pytest.approx(6.0)
        assert result[2].end_time_sec   == pytest.approx(19.9)

    def test_detect_scenes_fallback_single_scene_when_fewer_than_3(self, tmp_path):
        """Less than 3 raw scenes → whole video treated as 1 scene."""
        detector = self._make_detector(tmp_path)
        fake_video = tmp_path / "video.mp4"
        fake_video.write_bytes(b"fake")

        with patch.object(detector, "_run_scene_detection", return_value=[(0.0, 2.0)]), \
             patch.object(detector, "_get_duration", return_value=30.0), \
             patch.object(detector, "extract_keyframe", return_value=""):
            result = detector.detect_scenes(fake_video)

        assert len(result) == 1
        assert result[0].start_time_sec == 0.0
        assert result[0].end_time_sec   == pytest.approx(30.0)

    def test_detect_scenes_raises_for_missing_file(self, tmp_path):
        detector = self._make_detector(tmp_path)
        with pytest.raises(FileNotFoundError):
            detector.detect_scenes(tmp_path / "ghost.mp4")


# ─────────────────────────────────────────────────────────────────────────────
# TaskInput — input schema parsing
# ─────────────────────────────────────────────────────────────────────────────

class TestTaskInput:

    def test_required_fields_parsed(self):
        inp = TaskInput({"bucket": "media", "video_s3_key": "uploads/v.mp4"})
        assert inp.bucket == "media"
        assert inp.video_s3_key == "uploads/v.mp4"

    def test_asset_id_auto_generated_when_absent(self):
        inp = TaskInput({"bucket": "media", "video_s3_key": "uploads/v.mp4"})
        assert inp.asset_id.startswith("vid_")
        assert len(inp.asset_id) > 5

    def test_asset_id_uses_provided_value(self):
        inp = TaskInput({
            "bucket": "media",
            "video_s3_key": "uploads/v.mp4",
            "asset_id": "vid_custom_abc123",
        })
        assert inp.asset_id == "vid_custom_abc123"

    def test_proxy_s3_key_format(self):
        inp = TaskInput({
            "bucket": "media",
            "video_s3_key": "uploads/v.mp4",
            "asset_id": "vid_test_001",
        })
        assert inp.proxy_s3_key == "proxies/vid_test_001_proxy.mp4"

    def test_thumb_s3_key_format(self):
        inp = TaskInput({
            "bucket": "media",
            "video_s3_key": "uploads/v.mp4",
            "asset_id": "vid_test_001",
        })
        assert inp.thumb_s3_key(3) == "thumbnails/vid_test_001_scene_0003.jpg"

    def test_thumb_s3_key_zero_padded_4_digits(self):
        inp = TaskInput({"bucket": "b", "video_s3_key": "k", "asset_id": "vid_x"})
        assert "_scene_0000.jpg" in inp.thumb_s3_key(0)
        assert "_scene_0012.jpg" in inp.thumb_s3_key(12)
        assert "_scene_0099.jpg" in inp.thumb_s3_key(99)

    def test_custom_prefixes(self):
        inp = TaskInput({
            "bucket": "media",
            "video_s3_key": "uploads/v.mp4",
            "asset_id": "vid_x",
            "proxy_prefix": "my_proxies",
            "thumb_prefix": "my_thumbs",
        })
        assert inp.proxy_s3_key.startswith("my_proxies/")
        assert inp.thumb_s3_key(0).startswith("my_thumbs/")

    def test_missing_bucket_raises(self):
        with pytest.raises(ValueError, match="bucket"):
            TaskInput({"video_s3_key": "uploads/v.mp4"})

    def test_missing_video_s3_key_raises(self):
        with pytest.raises(ValueError, match="video_s3_key"):
            TaskInput({"bucket": "media"})


# ─────────────────────────────────────────────────────────────────────────────
# run_task — full pipeline output JSON schema
# ─────────────────────────────────────────────────────────────────────────────

class TestRunTaskOutputSchema:
    """
    run_task() must always return a dict matching the output JSON schema,
    regardless of success or failure.
    """

    def _make_inp(self) -> TaskInput:
        return TaskInput({
            "bucket":       "media",
            "video_s3_key": "uploads/beach.mp4",
            "asset_id":     "vid_beach_abc123",
        })

    def _make_scene_dicts(self, n: int = 3) -> List[dict]:
        return [
            {
                "scene_index":     i,
                "start_sec":       float(i * 5),
                "end_sec":         float(i * 5 + 5),
                "_thumb_local":    f"/tmp/scene_{i}.jpg",
                "keyframe_s3_key": f"thumbnails/vid_beach_abc123_scene_{i:04d}.jpg",
            }
            for i in range(n)
        ]

    def test_success_output_has_required_top_level_keys(self, tmp_path):
        inp = self._make_inp()
        storage = MagicMock()
        storage.download_file.return_value = True
        storage.upload_file.return_value = True
        storage.upload_bytes.return_value = True

        scenes = self._make_scene_dicts(3)

        # Write fake thumbnails so upload_bytes reads real files
        for s in scenes:
            Path(s["_thumb_local"]).parent.mkdir(parents=True, exist_ok=True)
            Path(s["_thumb_local"]).write_bytes(b"fake jpeg")

        with patch("ai_pipeline.ecs.entrypoint.step_download") as mock_dl, \
             patch("ai_pipeline.ecs.entrypoint.step_process", return_value=scenes) as mock_proc, \
             patch("ai_pipeline.ecs.entrypoint.step_upload") as mock_up, \
             patch("ai_pipeline.ecs.entrypoint.TaskWorkspace") as mock_ws:

            mock_ws.return_value.__enter__ = lambda s: MagicMock(proxy_path=MagicMock(exists=lambda: True))
            mock_ws.return_value.__exit__  = MagicMock(return_value=False)

            result = run_task(inp, storage)

        assert "asset_id" in result
        assert "status"   in result
        assert "scenes"   in result

    def test_success_status_value(self, tmp_path):
        inp = self._make_inp()
        storage = MagicMock(download_file=MagicMock(return_value=True),
                            upload_file=MagicMock(return_value=True),
                            upload_bytes=MagicMock(return_value=True))

        with patch("ai_pipeline.ecs.entrypoint.step_download"), \
             patch("ai_pipeline.ecs.entrypoint.step_process", return_value=self._make_scene_dicts()), \
             patch("ai_pipeline.ecs.entrypoint.step_upload"), \
             patch("ai_pipeline.ecs.entrypoint.TaskWorkspace") as mock_ws:

            mock_ws.return_value.__enter__ = lambda s: MagicMock(proxy_path=MagicMock(exists=lambda: True))
            mock_ws.return_value.__exit__  = MagicMock(return_value=False)

            result = run_task(inp, storage)

        assert result["status"] == "success"

    def test_failure_output_has_error_key(self):
        inp = self._make_inp()
        storage = MagicMock()

        with patch("ai_pipeline.ecs.entrypoint.step_download",
                   side_effect=RuntimeError("download failed")), \
             patch("ai_pipeline.ecs.entrypoint.TaskWorkspace") as mock_ws:

            ws_instance = MagicMock()
            mock_ws.return_value.__enter__ = lambda s: ws_instance
            mock_ws.return_value.__exit__  = MagicMock(return_value=False)

            result = run_task(inp, storage)

        assert result["status"] == "failed"
        assert "error" in result
        assert "download failed" in result["error"]

    def test_scenes_list_correct_length(self):
        inp = self._make_inp()
        storage = MagicMock()
        scenes = self._make_scene_dicts(5)

        with patch("ai_pipeline.ecs.entrypoint.step_download"), \
             patch("ai_pipeline.ecs.entrypoint.step_process", return_value=scenes), \
             patch("ai_pipeline.ecs.entrypoint.step_upload"), \
             patch("ai_pipeline.ecs.entrypoint.TaskWorkspace") as mock_ws:

            mock_ws.return_value.__enter__ = lambda s: MagicMock(proxy_path=MagicMock(exists=lambda: True))
            mock_ws.return_value.__exit__  = MagicMock(return_value=False)

            result = run_task(inp, storage)

        assert len(result["scenes"]) == 5

    def test_scene_dict_has_all_required_keys(self):
        inp = self._make_inp()
        storage = MagicMock()
        scenes = self._make_scene_dicts(2)

        with patch("ai_pipeline.ecs.entrypoint.step_download"), \
             patch("ai_pipeline.ecs.entrypoint.step_process", return_value=scenes), \
             patch("ai_pipeline.ecs.entrypoint.step_upload"), \
             patch("ai_pipeline.ecs.entrypoint.TaskWorkspace") as mock_ws:

            mock_ws.return_value.__enter__ = lambda s: MagicMock(proxy_path=MagicMock(exists=lambda: True))
            mock_ws.return_value.__exit__  = MagicMock(return_value=False)

            result = run_task(inp, storage)

        for scene in result["scenes"]:
            assert "scene_index"     in scene
            assert "start_sec"       in scene
            assert "end_sec"         in scene
            assert "keyframe_s3_key" in scene

    def test_scene_dict_does_not_contain_internal_thumb_local(self):
        """_thumb_local is an internal key and must be stripped from output."""
        inp = self._make_inp()
        storage = MagicMock()
        scenes = self._make_scene_dicts(2)

        with patch("ai_pipeline.ecs.entrypoint.step_download"), \
             patch("ai_pipeline.ecs.entrypoint.step_process", return_value=scenes), \
             patch("ai_pipeline.ecs.entrypoint.step_upload"), \
             patch("ai_pipeline.ecs.entrypoint.TaskWorkspace") as mock_ws:

            mock_ws.return_value.__enter__ = lambda s: MagicMock(proxy_path=MagicMock(exists=lambda: True))
            mock_ws.return_value.__exit__  = MagicMock(return_value=False)

            result = run_task(inp, storage)

        for scene in result["scenes"]:
            assert "_thumb_local" not in scene

    def test_asset_id_preserved_in_output(self):
        inp = self._make_inp()
        storage = MagicMock()

        with patch("ai_pipeline.ecs.entrypoint.step_download"), \
             patch("ai_pipeline.ecs.entrypoint.step_process", return_value=[]), \
             patch("ai_pipeline.ecs.entrypoint.step_upload"), \
             patch("ai_pipeline.ecs.entrypoint.TaskWorkspace") as mock_ws:

            mock_ws.return_value.__enter__ = lambda s: MagicMock(proxy_path=MagicMock(exists=lambda: False))
            mock_ws.return_value.__exit__  = MagicMock(return_value=False)

            result = run_task(inp, storage)

        assert result["asset_id"] == "vid_beach_abc123"

    def test_output_is_json_serializable(self):
        """Toàn bộ output phải serialize được thành JSON string."""
        inp = self._make_inp()
        storage = MagicMock()
        scenes = self._make_scene_dicts(3)

        with patch("ai_pipeline.ecs.entrypoint.step_download"), \
             patch("ai_pipeline.ecs.entrypoint.step_process", return_value=scenes), \
             patch("ai_pipeline.ecs.entrypoint.step_upload"), \
             patch("ai_pipeline.ecs.entrypoint.TaskWorkspace") as mock_ws:

            mock_ws.return_value.__enter__ = lambda s: MagicMock(proxy_path=MagicMock(exists=lambda: True))
            mock_ws.return_value.__exit__  = MagicMock(return_value=False)

            result = run_task(inp, storage)

        # Must not raise
        serialized = json.dumps(result)
        assert isinstance(serialized, str)
        reparsed = json.loads(serialized)
        assert reparsed["asset_id"] == inp.asset_id


# ─────────────────────────────────────────────────────────────────────────────
# step_build_output — unit test riêng
# ─────────────────────────────────────────────────────────────────────────────

class TestStepBuildOutput:

    def _inp(self):
        return TaskInput({"bucket": "b", "video_s3_key": "k", "asset_id": "vid_x"})

    def test_status_is_success(self):
        out = step_build_output(self._inp(), [], "proxies/x.mp4")
        assert out["status"] == "success"

    def test_proxy_key_in_output(self):
        out = step_build_output(self._inp(), [], "proxies/x.mp4")
        assert out["proxy_s3_key"] == "proxies/x.mp4"

    def test_scenes_stripped_of_internal_keys(self):
        scenes = [
            {
                "scene_index": 0, "start_sec": 0.0, "end_sec": 5.0,
                "_thumb_local": "/tmp/x.jpg",
                "keyframe_s3_key": "thumbnails/vid_x_scene_0000.jpg",
            }
        ]
        out = step_build_output(self._inp(), scenes, None)
        assert "_thumb_local" not in out["scenes"][0]

    def test_keyframe_s3_key_format_in_output(self):
        inp = self._inp()
        scenes = [
            {
                "scene_index": 1, "start_sec": 5.0, "end_sec": 10.0,
                "_thumb_local": None,
                "keyframe_s3_key": inp.thumb_s3_key(1),
            }
        ]
        out = step_build_output(inp, scenes, None)
        assert out["scenes"][0]["keyframe_s3_key"] == "thumbnails/vid_x_scene_0001.jpg"

    def test_empty_scenes_list(self):
        out = step_build_output(self._inp(), [], None)
        assert out["scenes"] == []

    def test_start_sec_and_end_sec_are_floats(self):
        scenes = [
            {
                "scene_index": 0, "start_sec": 0.0, "end_sec": 5.2,
                "_thumb_local": None,
                "keyframe_s3_key": "thumbnails/vid_x_scene_0000.jpg",
            }
        ]
        out = step_build_output(self._inp(), scenes, None)
        assert isinstance(out["scenes"][0]["start_sec"], float)
        assert isinstance(out["scenes"][0]["end_sec"], float)


# ─────────────────────────────────────────────────────────────────────────────
# _generate_asset_id helper
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateAssetId:

    def test_starts_with_vid_prefix(self):
        asset_id = _generate_asset_id("uploads/beach_video.mp4")
        assert asset_id.startswith("vid_")

    def test_stem_included_in_id(self):
        asset_id = _generate_asset_id("uploads/beach_video.mp4")
        assert "beach_video" in asset_id

    def test_unique_per_call(self):
        ids = {_generate_asset_id("uploads/v.mp4") for _ in range(10)}
        assert len(ids) == 10  # all unique

    def test_spaces_replaced(self):
        asset_id = _generate_asset_id("uploads/my video file.mp4")
        assert " " not in asset_id


# ─────────────────────────────────────────────────────────────────────────────
# ECS Workspace Cleanup
# ─────────────────────────────────────────────────────────────────────────────

def test_workspace_cleanup():
    """
    ECS task workspace must always be deleted when context exits.
    """

    with TaskWorkspace("cleanup_test") as ws:
        root = ws.root

        assert root.exists()

        dummy = root / "dummy.txt"
        dummy.write_text("hello")

        assert dummy.exists()

    assert not root.exists()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])