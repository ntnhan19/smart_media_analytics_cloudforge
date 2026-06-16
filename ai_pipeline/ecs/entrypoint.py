#!/usr/bin/env python3
"""
ECS Task Entrypoint — Video Scene Extraction Service

Orchestrates the full short-lived ECS task lifecycle:
  1. Parse JSON input config (--config-path or --config-json)
  2. Download source video from S3/MinIO to /tmp
  3. Create proxy video via FFmpeg (480p, CRF 28)
  4. Detect scenes via PySceneDetect; extract keyframe thumbnails
  5. Upload proxy + keyframe thumbnails back to S3/MinIO
  6. Write structured JSON result to --output-path or stdout
  7. Clean up /tmp working directory (no temp file leaks)

Input JSON schema:
    {
        "bucket":        "media",
        "video_s3_key":  "uploads/filename.mp4",
        "asset_id":      "vid_20240101_abc123",   // optional — auto-generated if absent
        "proxy_prefix":  "proxies/",              // optional — default "proxies/"
        "thumb_prefix":  "thumbnails/"            // optional — default "thumbnails/"
    }

Output JSON schema:
    {
        "asset_id":   "vid_20240101_abc123",
        "status":     "success" | "failed",
        "proxy_s3_key": "proxies/vid_20240101_abc123_proxy.mp4",
        "scenes": [
            {
                "scene_index":    0,
                "start_sec":      0.0,
                "end_sec":        5.2,
                "keyframe_s3_key": "thumbnails/vid_20240101_abc123_scene_0000.jpg"
            },
            ...
        ],
        "error": "..."    // only present on failure
    }

CLI usage:
    python entrypoint.py --config-path /tmp/input.json --output-path /tmp/result.json
    python entrypoint.py --config-json '{"bucket":"media","video_s3_key":"uploads/v.mp4"}'
"""

import argparse
import json
import logging
import os
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Logging setup (before any local imports so ECS CloudWatch captures everything) ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("entrypoint")


# ── Local imports (after logging so import errors are captured) ────────────────
try:
    from ai_pipeline.database.storage_client import StorageClientFactory, StorageClient
    from ai_pipeline.scene_detection.scene_detector import SceneDetector, VideoProcessor
except ImportError as exc:
    logger.error(f"Import error: {exc}")
    sys.exit(1)


# ── Constants ──────────────────────────────────────────────────────────────────

TMP_BASE = Path(os.getenv("TASK_TMP_DIR", "/tmp/ecs_task"))


# ── Input / Output schemas ─────────────────────────────────────────────────────

class TaskInput:
    """Parsed and validated task input configuration."""

    def __init__(self, raw: Dict[str, Any]):
        # Required
        self.bucket: str = _require(raw, "bucket")
        self.video_s3_key: str = _require(raw, "video_s3_key")

        # Optional with defaults
        self.asset_id: str = raw.get("asset_id") or _generate_asset_id(self.video_s3_key)
        self.proxy_prefix: str = raw.get("proxy_prefix", "proxies/").rstrip("/") + "/"
        self.thumb_prefix: str  = raw.get("thumb_prefix", "thumbnails/").rstrip("/") + "/"

    @property
    def proxy_s3_key(self) -> str:
        return f"{self.proxy_prefix}{self.asset_id}_proxy.mp4"

    def thumb_s3_key(self, scene_index: int) -> str:
        return f"{self.thumb_prefix}{self.asset_id}_scene_{scene_index:04d}.jpg"


def _require(d: Dict, key: str) -> str:
    val = d.get(key)
    if not val:
        raise ValueError(f"Missing required input field: '{key}'")
    return val


def _generate_asset_id(video_key: str) -> str:
    stem = Path(video_key).stem.replace(" ", "_")[:40]
    short = uuid.uuid4().hex[:8]
    return f"vid_{stem}_{short}"


# ── Task working directory ─────────────────────────────────────────────────────

class TaskWorkspace:
    """
    Manages the /tmp/<task_id>/ working directory.
    Guaranteed cleanup via context manager — no temp files left behind.
    """

    def __init__(self, asset_id: str):
        self.root = TMP_BASE / asset_id
        self.root.mkdir(parents=True, exist_ok=True)
        self.video_path   = self.root / "source.mp4"
        self.proxy_path   = self.root / "proxy.mp4"
        self.thumbs_dir   = self.root / "thumbnails"
        self.thumbs_dir.mkdir(parents=True, exist_ok=True)

    def cleanup(self) -> None:
        """Remove the entire working directory tree."""
        try:
            if self.root.exists():
                shutil.rmtree(self.root)
                logger.info(f"[Workspace] Cleaned up {self.root}")
        except Exception as exc:
            logger.warning(f"[Workspace] Cleanup failed for {self.root}: {exc}")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.cleanup()


# ── Core pipeline steps ────────────────────────────────────────────────────────

def step_download(storage: StorageClient, inp: TaskInput, ws: TaskWorkspace) -> None:
    """Download source video from S3/MinIO to local /tmp."""
    logger.info(f"[Step 1/4] Downloading s3://{inp.bucket}/{inp.video_s3_key}")
    ok = storage.download_file(inp.video_s3_key, str(ws.video_path))
    if not ok or not ws.video_path.exists():
        raise RuntimeError(
            f"Failed to download video: s3://{inp.bucket}/{inp.video_s3_key}"
        )
    size_mb = ws.video_path.stat().st_size / (1024 * 1024)
    logger.info(f"[Step 1/4] Downloaded {size_mb:.1f} MB → {ws.video_path}")


def step_process(inp: TaskInput, ws: TaskWorkspace) -> List[Dict[str, Any]]:
    """
    Run FFmpeg proxy encoding + PySceneDetect.

    Returns list of scene dicts with local thumbnail paths.
    """
    logger.info("[Step 2/4] Creating proxy video + detecting scenes")

    # ── FFmpeg proxy ──────────────────────────────────────────────────────────
    processor = VideoProcessor()
    proxy_ok = processor.create_proxy(ws.video_path, ws.proxy_path)
    if not proxy_ok:
        logger.warning("[Step 2/4] Proxy creation failed — using original video for scene detection")
        working_video = ws.video_path
    else:
        logger.info(f"[Step 2/4] Proxy created: {ws.proxy_path}")
        working_video = ws.proxy_path

    # ── Scene detection + keyframe extraction ────────────────────────────────
    detector = SceneDetector(thumbnails_dir=ws.thumbs_dir)
    scene_data_list = detector.detect_scenes(working_video)

    scenes: List[Dict[str, Any]] = []
    for sd in scene_data_list:
        thumb_local = Path(sd.keyframe_path) if sd.keyframe_path else None
        scenes.append({
            "scene_index":   sd.scene_index,
            "start_sec":     round(sd.start_time_sec, 3),
            "end_sec":       round(sd.end_time_sec, 3),
            "_thumb_local":  str(thumb_local) if thumb_local else None,
            "keyframe_s3_key": inp.thumb_s3_key(sd.scene_index),  # pre-fill key
        })

    logger.info(f"[Step 2/4] Detected {len(scenes)} scenes")
    return scenes


def step_upload(
    storage: StorageClient,
    inp: TaskInput,
    ws: TaskWorkspace,
    scenes: List[Dict[str, Any]],
) -> None:
    """Upload proxy video + all keyframe thumbnails to S3/MinIO."""
    logger.info("[Step 3/4] Uploading proxy + thumbnails")

    # Upload proxy
    if ws.proxy_path.exists():
        ok = storage.upload_file(str(ws.proxy_path), inp.proxy_s3_key)
        if not ok:
            raise RuntimeError(f"Failed to upload proxy: {inp.proxy_s3_key}")
        logger.info(f"[Step 3/4] Proxy uploaded → {inp.proxy_s3_key}")
    else:
        logger.warning("[Step 3/4] No proxy file found — skipping proxy upload")

    # Upload thumbnails via upload_bytes (no extra disk I/O after cv2.imwrite)
    uploaded = 0
    failed   = 0
    for scene in scenes:
        local_path = scene.get("_thumb_local")
        s3_key     = scene["keyframe_s3_key"]

        if not local_path or not Path(local_path).exists():
            logger.warning(f"[Step 3/4] Thumbnail missing for scene {scene['scene_index']}")
            failed += 1
            continue

        try:
            jpeg_bytes = Path(local_path).read_bytes()
            ok = storage.upload_bytes(jpeg_bytes, s3_key, content_type="image/jpeg")
            if ok:
                uploaded += 1
            else:
                failed += 1
                logger.warning(f"[Step 3/4] Failed to upload thumbnail: {s3_key}")
        except Exception as exc:
            failed += 1
            logger.error(f"[Step 3/4] Thumbnail upload error ({s3_key}): {exc}")

    logger.info(f"[Step 3/4] Thumbnails: {uploaded} uploaded, {failed} failed")


def step_build_output(
    inp: TaskInput,
    scenes: List[Dict[str, Any]],
    proxy_s3_key: Optional[str],
) -> Dict[str, Any]:
    """Assemble the final output JSON (strips internal _thumb_local key)."""
    clean_scenes = [
        {
            "scene_index":     s["scene_index"],
            "start_sec":       s["start_sec"],
            "end_sec":         s["end_sec"],
            "keyframe_s3_key": s["keyframe_s3_key"],
        }
        for s in scenes
    ]
    return {
        "asset_id":     inp.asset_id,
        "status":       "success",
        "proxy_s3_key": proxy_s3_key,
        "scenes":       clean_scenes,
    }


# ── Main orchestrator ──────────────────────────────────────────────────────────

def run_task(inp: TaskInput, storage: StorageClient) -> Dict[str, Any]:
    """
    Execute the full ECS task pipeline.
    Always cleans up /tmp workspace on exit (success or failure).
    """
    with TaskWorkspace(inp.asset_id) as ws:
        try:
            # Step 1 — Download
            step_download(storage, inp, ws)

            # Step 2 — Process
            scenes = step_process(inp, ws)

            # Step 3 — Upload
            step_upload(storage, inp, ws, scenes)

            # Step 4 — Build output
            proxy_key = inp.proxy_s3_key if ws.proxy_path.exists() else None
            result = step_build_output(inp, scenes, proxy_key)

            logger.info(
                f"[Step 4/4] Task complete: asset_id={inp.asset_id}, "
                f"scenes={len(scenes)}"
            )
            return result

        except Exception as exc:
            logger.error(f"Task failed: {exc}", exc_info=True)
            return {
                "asset_id": inp.asset_id,
                "status":   "failed",
                "error":    str(exc),
                "scenes":   [],
            }
        # TaskWorkspace.__exit__ calls cleanup() here — always runs


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ECS Task — Video Scene Extraction Service"
    )

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--config-path",
        metavar="PATH",
        help="Path to JSON input config file",
    )
    input_group.add_argument(
        "--config-json",
        metavar="JSON",
        help="Inline JSON input config string",
    )

    parser.add_argument(
        "--output-path",
        metavar="PATH",
        default=None,
        help="Write JSON result to this file (default: stdout)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # ── Load input ─────────────────────────────────────────────────────────────
    try:
        if args.config_path:
            raw = json.loads(Path(args.config_path).read_text())
        else:
            raw = json.loads(args.config_json)
    except (json.JSONDecodeError, FileNotFoundError) as exc:
        logger.error(f"Failed to parse input config: {exc}")
        sys.exit(1)

    try:
        inp = TaskInput(raw)
    except ValueError as exc:
        logger.error(f"Invalid input config: {exc}")
        sys.exit(1)

    # ── Build storage client ───────────────────────────────────────────────────
    try:
        storage = StorageClientFactory.from_env()
    except Exception as exc:
        logger.error(f"Failed to initialize storage client: {exc}")
        sys.exit(1)

    # ── Execute ────────────────────────────────────────────────────────────────
    result = run_task(inp, storage)

    # ── Emit output JSON ───────────────────────────────────────────────────────
    output_json = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output_path:
        out = Path(args.output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(output_json, encoding="utf-8")
        logger.info(f"Result written to {args.output_path}")
    else:
        # stdout — consumed by Step Functions / ECS task result
        print(output_json)

    # Exit code reflects task status for ECS / Step Functions error handling
    sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()