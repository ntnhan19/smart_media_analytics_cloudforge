"""
Unit Tests — StorageClient (MinIO + S3)

Tests đầy đủ cho các API:
  - upload_file()
  - upload_bytes()
  - download_file()
  - delete_file()
  - file_exists()

Tất cả các test đều sử dụng mock — không cần kết nối thực tế.

Run:
    pytest ai_pipeline/tests/test_storage.py -v
"""

import io
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from ai_pipeline.database.storage_client import (
    MinioStorageClient,
    S3StorageClient,
    StorageClientFactory,
    _guess_content_type,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers / Fixtures
# ─────────────────────────────────────────────────────────────────────────────

BUCKET = "test-bucket"
REMOTE_KEY = "uploads/video.mp4"
THUMB_KEY = "thumbnails/scene_0001.jpg"
PROXY_KEY = "proxies/video_proxy.mp4"

SAMPLE_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 100  # fake JPEG header + padding


def _make_minio_client() -> MinioStorageClient:
    """MinioStorageClient với Minio SDK hoàn toàn bị mock."""
    with patch("ai_pipeline.database.storage_client.MinioStorageClient.__init__",
               return_value=None):
        client = MinioStorageClient.__new__(MinioStorageClient)
        client._bucket = BUCKET
        client._client = MagicMock()
        return client


def _make_s3_client() -> S3StorageClient:
    """S3StorageClient với boto3 hoàn toàn bị mock."""
    with patch("ai_pipeline.database.storage_client.S3StorageClient.__init__",
               return_value=None):
        client = S3StorageClient.__new__(S3StorageClient)
        client._bucket = BUCKET
        client._s3 = MagicMock()
        return client


@pytest.fixture
def minio() -> MinioStorageClient:
    return _make_minio_client()


@pytest.fixture
def s3() -> S3StorageClient:
    return _make_s3_client()


@pytest.fixture
def tmp_video(tmp_path: Path) -> Path:
    """Fake local video file."""
    f = tmp_path / "video.mp4"
    f.write_bytes(b"fake mp4 content")
    return f


@pytest.fixture
def tmp_thumb(tmp_path: Path) -> Path:
    """Fake local JPEG thumbnail."""
    f = tmp_path / "thumb.jpg"
    f.write_bytes(SAMPLE_BYTES)
    return f


# ─────────────────────────────────────────────────────────────────────────────
# MinioStorageClient Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestMinioUploadFile:

    def test_upload_file_returns_true_on_success(self, minio, tmp_video):
        minio._client.fput_object.return_value = None  # SDK returns None
        ok = minio.upload_file(str(tmp_video), PROXY_KEY)
        assert ok is True

    def test_upload_file_calls_fput_object_with_correct_args(self, minio, tmp_video):
        minio.upload_file(str(tmp_video), PROXY_KEY)
        minio._client.fput_object.assert_called_once_with(
            BUCKET, PROXY_KEY, str(tmp_video), content_type="video/mp4"
        )

    def test_upload_file_returns_false_on_sdk_error(self, minio, tmp_video):
        minio._client.fput_object.side_effect = Exception("connection refused")
        ok = minio.upload_file(str(tmp_video), PROXY_KEY)
        assert ok is False

    def test_upload_file_jpeg_content_type(self, minio, tmp_thumb):
        minio.upload_file(str(tmp_thumb), THUMB_KEY)
        _, kwargs = minio._client.fput_object.call_args
        positional = minio._client.fput_object.call_args.args
        # content_type passed as keyword or positional
        call_kwargs = minio._client.fput_object.call_args.kwargs
        assert call_kwargs.get("content_type") == "image/jpeg"


class TestMinioUploadBytes:

    def test_upload_bytes_returns_true_on_success(self, minio):
        minio._client.put_object.return_value = None
        ok = minio.upload_bytes(SAMPLE_BYTES, THUMB_KEY, content_type="image/jpeg")
        assert ok is True

    def test_upload_bytes_calls_put_object(self, minio):
        minio.upload_bytes(SAMPLE_BYTES, THUMB_KEY, content_type="image/jpeg")
        call_args = minio._client.put_object.call_args
        assert call_args.kwargs["content_type"] == "image/jpeg"
        assert call_args.kwargs["length"] == len(SAMPLE_BYTES)

    def test_upload_bytes_sends_correct_bucket_and_key(self, minio):
        minio.upload_bytes(SAMPLE_BYTES, THUMB_KEY)
        call_args = minio._client.put_object.call_args
        assert call_args.args[0] == BUCKET
        assert call_args.args[1] == THUMB_KEY

    def test_upload_bytes_wraps_data_in_bytesio(self, minio):
        """SDK must receive a file-like object, not raw bytes."""
        minio.upload_bytes(SAMPLE_BYTES, THUMB_KEY)
        call_args = minio._client.put_object.call_args
        stream = call_args.kwargs["data"]
        assert hasattr(stream, "read"), "data must be a file-like object"
        assert stream.read() == SAMPLE_BYTES

    def test_upload_bytes_returns_false_on_sdk_error(self, minio):
        minio._client.put_object.side_effect = RuntimeError("timeout")
        ok = minio.upload_bytes(SAMPLE_BYTES, THUMB_KEY)
        assert ok is False

    def test_upload_bytes_default_content_type(self, minio):
        minio.upload_bytes(b"data", "misc/file.bin")
        call_kwargs = minio._client.put_object.call_args.kwargs
        assert call_kwargs["content_type"] == "application/octet-stream"


class TestMinioDownloadFile:

    def test_download_file_returns_true_on_success(self, minio, tmp_path):
        local = str(tmp_path / "downloaded.mp4")
        ok = minio.download_file(REMOTE_KEY, local)
        assert ok is True

    def test_download_file_calls_fget_object(self, minio, tmp_path):
        local = str(tmp_path / "downloaded.mp4")
        minio.download_file(REMOTE_KEY, local)
        minio._client.fget_object.assert_called_once_with(BUCKET, REMOTE_KEY, local)

    def test_download_file_creates_parent_directory(self, minio, tmp_path):
        deep_path = str(tmp_path / "a" / "b" / "c" / "video.mp4")
        minio.download_file(REMOTE_KEY, deep_path)
        assert Path(deep_path).parent.exists()

    def test_download_file_returns_false_on_sdk_error(self, minio, tmp_path):
        minio._client.fget_object.side_effect = Exception("no such key")
        ok = minio.download_file(REMOTE_KEY, str(tmp_path / "v.mp4"))
        assert ok is False


class TestMinioDeleteFile:

    def test_delete_file_returns_true_on_success(self, minio):
        ok = minio.delete_file(PROXY_KEY)
        assert ok is True

    def test_delete_file_calls_remove_object(self, minio):
        minio.delete_file(PROXY_KEY)
        minio._client.remove_object.assert_called_once_with(BUCKET, PROXY_KEY)

    def test_delete_file_returns_true_when_key_not_found(self, minio):
        """Idempotent delete — missing key must not raise."""
        minio._client.remove_object.side_effect = Exception("NoSuchKey: not found")
        ok = minio.delete_file("ghost/key.mp4")
        assert ok is True

    def test_delete_file_returns_false_on_real_error(self, minio):
        minio._client.remove_object.side_effect = Exception("access denied")
        ok = minio.delete_file(PROXY_KEY)
        assert ok is False

    def test_delete_thumbnail_key(self, minio):
        ok = minio.delete_file(THUMB_KEY)
        assert ok is True
        minio._client.remove_object.assert_called_with(BUCKET, THUMB_KEY)


class TestMinioFileExists:

    def test_file_exists_returns_true_when_object_found(self, minio):
        minio._client.stat_object.return_value = MagicMock()  # any truthy value
        assert minio.file_exists(PROXY_KEY) is True

    def test_file_exists_calls_stat_object(self, minio):
        minio._client.stat_object.return_value = MagicMock()
        minio.file_exists(PROXY_KEY)
        minio._client.stat_object.assert_called_once_with(BUCKET, PROXY_KEY)

    def test_file_exists_returns_false_when_key_missing(self, minio):
        minio._client.stat_object.side_effect = Exception("NoSuchKey: does not exist")
        assert minio.file_exists("missing/key.mp4") is False

    def test_file_exists_returns_false_for_not_found_error(self, minio):
        minio._client.stat_object.side_effect = Exception("not found")
        assert minio.file_exists("anything.mp4") is False


# ─────────────────────────────────────────────────────────────────────────────
# S3StorageClient Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestS3UploadFile:

    def test_upload_file_returns_true_on_success(self, s3, tmp_video):
        ok = s3.upload_file(str(tmp_video), PROXY_KEY)
        assert ok is True

    def test_upload_file_calls_boto3_upload_file(self, s3, tmp_video):
        s3.upload_file(str(tmp_video), PROXY_KEY)
        s3._s3.upload_file.assert_called_once()
        args = s3._s3.upload_file.call_args
        assert args.args[0] == str(tmp_video)
        assert args.args[1] == BUCKET
        assert args.args[2] == PROXY_KEY

    def test_upload_file_passes_content_type_as_extra_args(self, s3, tmp_video):
        s3.upload_file(str(tmp_video), PROXY_KEY)
        kwargs = s3._s3.upload_file.call_args.kwargs
        assert "ExtraArgs" in kwargs
        assert kwargs["ExtraArgs"]["ContentType"] == "video/mp4"

    def test_upload_file_returns_false_on_error(self, s3, tmp_video):
        s3._s3.upload_file.side_effect = Exception("NoCredentialsError")
        ok = s3.upload_file(str(tmp_video), PROXY_KEY)
        assert ok is False


class TestS3UploadBytes:

    def test_upload_bytes_returns_true_on_success(self, s3):
        ok = s3.upload_bytes(SAMPLE_BYTES, THUMB_KEY, content_type="image/jpeg")
        assert ok is True

    def test_upload_bytes_calls_put_object(self, s3):
        s3.upload_bytes(SAMPLE_BYTES, THUMB_KEY, content_type="image/jpeg")
        s3._s3.put_object.assert_called_once()

    def test_upload_bytes_correct_bucket_and_key(self, s3):
        s3.upload_bytes(SAMPLE_BYTES, THUMB_KEY)
        call_kwargs = s3._s3.put_object.call_args.kwargs
        assert call_kwargs["Bucket"] == BUCKET
        assert call_kwargs["Key"] == THUMB_KEY

    def test_upload_bytes_passes_body(self, s3):
        s3.upload_bytes(SAMPLE_BYTES, THUMB_KEY)
        call_kwargs = s3._s3.put_object.call_args.kwargs
        assert call_kwargs["Body"] == SAMPLE_BYTES

    def test_upload_bytes_passes_content_type(self, s3):
        s3.upload_bytes(SAMPLE_BYTES, THUMB_KEY, content_type="image/jpeg")
        call_kwargs = s3._s3.put_object.call_args.kwargs
        assert call_kwargs["ContentType"] == "image/jpeg"

    def test_upload_bytes_returns_false_on_error(self, s3):
        s3._s3.put_object.side_effect = Exception("AccessDenied")
        ok = s3.upload_bytes(SAMPLE_BYTES, THUMB_KEY)
        assert ok is False


class TestS3DownloadFile:

    def test_download_file_returns_true_on_success(self, s3, tmp_path):
        ok = s3.download_file(REMOTE_KEY, str(tmp_path / "v.mp4"))
        assert ok is True

    def test_download_file_calls_boto3_download(self, s3, tmp_path):
        local = str(tmp_path / "v.mp4")
        s3.download_file(REMOTE_KEY, local)
        s3._s3.download_file.assert_called_once_with(BUCKET, REMOTE_KEY, local)

    def test_download_file_returns_false_on_error(self, s3, tmp_path):
        s3._s3.download_file.side_effect = Exception("NoSuchKey")
        ok = s3.download_file("missing.mp4", str(tmp_path / "v.mp4"))
        assert ok is False


class TestS3DeleteFile:

    def test_delete_file_returns_true_on_success(self, s3):
        ok = s3.delete_file(PROXY_KEY)
        assert ok is True

    def test_delete_file_calls_delete_object(self, s3):
        s3.delete_file(PROXY_KEY)
        s3._s3.delete_object.assert_called_once_with(Bucket=BUCKET, Key=PROXY_KEY)

    def test_delete_file_idempotent_missing_key(self, s3):
        """S3 delete_object is inherently idempotent — always returns True."""
        s3._s3.delete_object.return_value = {"ResponseMetadata": {"HTTPStatusCode": 204}}
        ok = s3.delete_file("ghost_key.mp4")
        assert ok is True

    def test_delete_file_returns_false_on_real_error(self, s3):
        s3._s3.delete_object.side_effect = Exception("InternalError")
        ok = s3.delete_file(PROXY_KEY)
        assert ok is False


class TestS3FileExists:

    def test_file_exists_returns_true_when_object_found(self, s3):
        s3._s3.head_object.return_value = {"ContentLength": 1024}
        assert s3.file_exists(PROXY_KEY) is True

    def test_file_exists_calls_head_object(self, s3):
        s3._s3.head_object.return_value = {}
        s3.file_exists(PROXY_KEY)
        s3._s3.head_object.assert_called_once_with(Bucket=BUCKET, Key=PROXY_KEY)

    def test_file_exists_returns_false_on_404(self, s3):
        from botocore.exceptions import ClientError
        error_response = {"Error": {"Code": "404", "Message": "Not Found"}}
        s3._s3.head_object.side_effect = ClientError(error_response, "HeadObject")
        assert s3.file_exists("missing.mp4") is False

    def test_file_exists_returns_false_on_no_such_key(self, s3):
        from botocore.exceptions import ClientError
        error_response = {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}}
        s3._s3.head_object.side_effect = ClientError(error_response, "HeadObject")
        assert s3.file_exists("also_missing.mp4") is False


# ─────────────────────────────────────────────────────────────────────────────
# StorageClientFactory Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestStorageClientFactory:

    def test_factory_builds_minio_client(self, monkeypatch):
        monkeypatch.setenv("STORAGE_BACKEND", "minio")
        monkeypatch.setenv("MINIO_ENDPOINT", "localhost:9000")
        monkeypatch.setenv("MINIO_ACCESS_KEY", "minioadmin")
        monkeypatch.setenv("MINIO_SECRET_KEY", "minioadmin")
        monkeypatch.setenv("MINIO_BUCKET", "media")

        with patch.object(MinioStorageClient, "__init__", return_value=None) as mock_init:
            client = StorageClientFactory.from_env()
            assert isinstance(client, MinioStorageClient)

    def test_factory_builds_s3_client(self, monkeypatch):
        monkeypatch.setenv("STORAGE_BACKEND", "s3")
        monkeypatch.setenv("AWS_S3_BUCKET", "my-media-bucket")

        with patch.object(S3StorageClient, "__init__", return_value=None):
            client = StorageClientFactory.from_env()
            assert isinstance(client, S3StorageClient)

    def test_factory_defaults_to_minio(self, monkeypatch):
        monkeypatch.delenv("STORAGE_BACKEND", raising=False)
        monkeypatch.setenv("MINIO_ENDPOINT", "localhost:9000")
        monkeypatch.setenv("MINIO_ACCESS_KEY", "k")
        monkeypatch.setenv("MINIO_SECRET_KEY", "s")
        monkeypatch.setenv("MINIO_BUCKET", "b")

        with patch.object(MinioStorageClient, "__init__", return_value=None):
            client = StorageClientFactory.from_env()
            assert isinstance(client, MinioStorageClient)

    def test_factory_raises_on_unknown_backend(self, monkeypatch):
        monkeypatch.setenv("STORAGE_BACKEND", "gcs")
        with pytest.raises(ValueError, match="Unknown STORAGE_BACKEND"):
            StorageClientFactory.from_env()


# ─────────────────────────────────────────────────────────────────────────────
# _guess_content_type helper
# ─────────────────────────────────────────────────────────────────────────────

class TestGuessContentType:

    @pytest.mark.parametrize("suffix,expected", [
        (".mp4",  "video/mp4"),
        (".mov",  "video/quicktime"),
        (".avi",  "video/x-msvideo"),
        (".mkv",  "video/x-matroska"),
        (".webm", "video/webm"),
        (".jpg",  "image/jpeg"),
        (".jpeg", "image/jpeg"),
        (".png",  "image/png"),
        (".wav",  "audio/wav"),
        (".json", "application/json"),
        (".xyz",  "application/octet-stream"),  # unknown → fallback
        ("",      "application/octet-stream"),  # no extension
    ])
    def test_content_type_mapping(self, suffix, expected):
        assert _guess_content_type(suffix) == expected

    def test_uppercase_suffix(self):
        """Extension lookup must be case-insensitive."""
        assert _guess_content_type(".MP4") == "video/mp4"
        assert _guess_content_type(".JPG") == "image/jpeg"


# ─────────────────────────────────────────────────────────────────────────────
# Cross-client contract tests (same behaviour expected from both)
# ─────────────────────────────────────────────────────────────────────────────

class TestStorageClientContract:
    """
    Both MinIO and S3 must honour the same behaviour contract.
    Parameterized so a new backend only needs to be added here.
    """

    @pytest.fixture(params=["minio", "s3"])
    def storage(self, request, minio, s3):
        return minio if request.param == "minio" else s3

    def test_upload_bytes_empty_data(self, storage):
        """Uploading zero bytes must not raise — returns bool."""
        result = storage.upload_bytes(b"", "empty/file.bin")
        assert isinstance(result, bool)

    def test_delete_file_returns_bool(self, storage):
        result = storage.delete_file(PROXY_KEY)
        assert isinstance(result, bool)

    def test_file_exists_returns_bool(self, storage):
        # Configure both mocks for "found" scenario
        if isinstance(storage, MinioStorageClient):
            storage._client.stat_object.return_value = MagicMock()
        else:
            storage._s3.head_object.return_value = {}
        result = storage.file_exists(PROXY_KEY)
        assert isinstance(result, bool)

    def test_upload_file_returns_bool(self, storage, tmp_video):
        result = storage.upload_file(str(tmp_video), REMOTE_KEY)
        assert isinstance(result, bool)

# ─────────────────────────────────────────────────────────────────────────────
# Integration Tests (Real MinIO)
# Run:
#   pytest test_storage.py -m integration
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
def test_minio_upload_download_real(tmp_path):
    """
    Real MinIO integration test.

    Requires:
        MINIO_ENDPOINT
        MINIO_ACCESS_KEY
        MINIO_SECRET_KEY
        MINIO_BUCKET
    """

    endpoint = os.getenv("MINIO_ENDPOINT")
    access_key = os.getenv("MINIO_ACCESS_KEY")
    secret_key = os.getenv("MINIO_SECRET_KEY")
    bucket = os.getenv("MINIO_BUCKET")

    if not all([endpoint, access_key, secret_key, bucket]):
        pytest.skip("MinIO integration env vars not configured")

    storage = MinioStorageClient(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        bucket=bucket,
        secure=False,
    )

    key = "integration/test_video.txt"

    source = tmp_path / "source.txt"
    source.write_text("hello integration")

    assert storage.upload_file(str(source), key)
    assert storage.file_exists(key)

    downloaded = tmp_path / "downloaded.txt"

    assert storage.download_file(key, str(downloaded))
    assert downloaded.read_text() == "hello integration"

    assert storage.delete_file(key)


@pytest.mark.integration
def test_minio_upload_bytes_real():
    """
    Verify upload_bytes + file_exists + delete_file against real MinIO.
    """

    endpoint = os.getenv("MINIO_ENDPOINT")
    access_key = os.getenv("MINIO_ACCESS_KEY")
    secret_key = os.getenv("MINIO_SECRET_KEY")
    bucket = os.getenv("MINIO_BUCKET")

    if not all([endpoint, access_key, secret_key, bucket]):
        pytest.skip("MinIO integration env vars not configured")

    storage = MinioStorageClient(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        bucket=bucket,
        secure=False,
    )

    key = "integration/test_bytes.jpg"

    data = b"fake thumbnail bytes"

    assert storage.upload_bytes(
        data,
        key,
        content_type="image/jpeg",
    )

    assert storage.file_exists(key)

    assert storage.delete_file(key)

    assert storage.file_exists(key) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])