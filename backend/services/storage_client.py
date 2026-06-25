"""
Storage Client — Cloud Storage Adapter for S3 / MinIO

Provides a unified StorageClient interface for:
- Uploading files (from path or raw bytes)
- Downloading files
- Checking existence
- Deleting files

Concrete implementations:
- MinioStorageClient  (MinIO / self-hosted S3-compatible)
- S3StorageClient     (AWS S3)
"""

import io
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ── Abstract Base ─────────────────────────────────────────────────────────────

class StorageClient(ABC):
    """
    Unified interface for cloud blob storage.
    All paths are *remote* keys (e.g. "uploads/video.mp4"),
    not local filesystem paths.
    """

    @abstractmethod
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        Upload a local file to remote storage.

        Args:
            local_path:  Absolute or relative path on the local filesystem.
            remote_path: Destination key in the bucket.

        Returns:
            True on success, False on failure.
        """

    @abstractmethod
    def upload_bytes(self, data: bytes, remote_path: str,
                     content_type: str = "application/octet-stream") -> bool:
        """
        Upload raw bytes directly to remote storage without writing to disk.
        Ideal for in-memory thumbnails / JPEG frames.

        Args:
            data:         Raw bytes to upload.
            remote_path:  Destination key in the bucket.
            content_type: MIME type (default: application/octet-stream).
                          Use "image/jpeg" for JPEG thumbnails.

        Returns:
            True on success, False on failure.
        """

    @abstractmethod
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        Download a remote object to a local path.

        Args:
            remote_path: Source key in the bucket.
            local_path:  Destination path on the local filesystem.

        Returns:
            True on success, False on failure.
        """

    @abstractmethod
    def delete_file(self, remote_path: str) -> bool:
        """
        Delete a single object from remote storage.
        Used for cleaning up proxy videos and thumbnails when an Asset is deleted.

        Args:
            remote_path: Key of the object to delete.

        Returns:
            True on success (including when the key does not exist), False on error.
        """

    @abstractmethod
    def file_exists(self, remote_path: str) -> bool:
        """
        Check whether an object exists in remote storage.
        Useful for idempotent uploads and pre-flight checks.

        Args:
            remote_path: Key to check.

        Returns:
            True if the object exists, False otherwise.
        """


# ── MinIO Implementation ──────────────────────────────────────────────────────

class MinioStorageClient(StorageClient):
    """
    Storage adapter for MinIO (and any S3-compatible endpoint).

    Environment variables (read by from_env()):
        MINIO_ENDPOINT   — host:port, e.g. "localhost:9000"
        MINIO_ACCESS_KEY — access key ID
        MINIO_SECRET_KEY — secret access key
        MINIO_BUCKET     — default bucket name
        MINIO_SECURE     — "true" | "false"  (default: "false")
    """

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
    ):
        try:
            from minio import Minio
            from minio.error import S3Error  # noqa: F401  (kept for except clauses)
        except ImportError as exc:
            raise ImportError(
                "minio package is required: pip install minio"
            ) from exc

        self._bucket = bucket
        self._access_key = access_key
        self._secret_key = secret_key
        self._secure = secure
        self._client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self._ensure_bucket()

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def from_env(cls) -> "MinioStorageClient":
        """Construct from environment variables."""
        # Normalize endpoint (remove http/https prefix if passed)
        endpoint = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
        if "://" in endpoint:
            endpoint = endpoint.split("://")[1]
            
        return cls(
            endpoint=endpoint,
            access_key=os.environ.get("MINIO_ROOT_USER") or os.environ.get("MINIO_ACCESS_KEY", "echoscene"),
            secret_key=os.environ.get("MINIO_ROOT_PASSWORD") or os.environ.get("MINIO_SECRET_KEY", "echoscene_dev_password"),
            bucket=os.environ.get("MINIO_BUCKET_MEDIA", "media"),
            secure=os.getenv("MINIO_USE_SSL", "false").lower() == "true",
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _ensure_bucket(self) -> None:
        """Create the bucket if it does not exist."""
        try:
            if not self._client.bucket_exists(self._bucket):
                self._client.make_bucket(self._bucket)
                logger.info(f"[MinIO] Bucket created: {self._bucket}")
        except Exception as exc:
            logger.warning(f"[MinIO] Could not ensure bucket '{self._bucket}': {exc}")

    # ── StorageClient interface ───────────────────────────────────────────────

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        try:
            local = Path(local_path)
            content_type = _guess_content_type(local.suffix)
            self._client.fput_object(
                self._bucket, remote_path, local_path,
                content_type=content_type,
            )
            logger.info(f"[MinIO] Uploaded {local_path} → {remote_path}")
            return True
        except Exception as exc:
            logger.error(f"[MinIO] upload_file failed ({remote_path}): {exc}")
            return False

    def upload_bytes(self, data: bytes, remote_path: str,
                     content_type: str = "application/octet-stream") -> bool:
        try:
            stream = io.BytesIO(data)
            self._client.put_object(
                self._bucket, remote_path,
                data=stream,
                length=len(data),
                content_type=content_type,
            )
            logger.info(f"[MinIO] Uploaded {len(data)} bytes → {remote_path}")
            return True
        except Exception as exc:
            logger.error(f"[MinIO] upload_bytes failed ({remote_path}): {exc}")
            return False

    def download_file(self, remote_path: str, local_path: str) -> bool:
        try:
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            self._client.fget_object(self._bucket, remote_path, local_path)
            logger.info(f"[MinIO] Downloaded {remote_path} → {local_path}")
            return True
        except Exception as exc:
            logger.error(f"[MinIO] download_file failed ({remote_path}): {exc}")
            return False

    def delete_file(self, remote_path: str) -> bool:
        try:
            self._client.remove_object(self._bucket, remote_path)
            logger.info(f"[MinIO] Deleted {remote_path}")
            return True
        except Exception as exc:
            # Treat "not found" (NoSuchKey) as success — idempotent delete
            err_str = str(exc).lower()
            if "nosuchkey" in err_str or "not found" in err_str or "does not exist" in err_str:
                logger.debug(f"[MinIO] delete_file: key not found (idempotent OK): {remote_path}")
                return True
            logger.error(f"[MinIO] delete_file failed ({remote_path}): {exc}")
            return False

    def file_exists(self, remote_path: str) -> bool:
        try:
            self._client.stat_object(self._bucket, remote_path)
            return True
        except Exception as exc:
            err_str = str(exc).lower()
            if "nosuchkey" in err_str or "not found" in err_str or "does not exist" in err_str:
                return False
            logger.error(f"[MinIO] file_exists check failed ({remote_path}): {exc}")
            return False

    def get_presigned_url(self, remote_path: str, expires_seconds: int = 3600) -> str:
        """Generate a presigned GET URL for an object."""
        try:
            from datetime import timedelta
            from minio import Minio

            # Create an external-facing client so the signature is computed for 'localhost:9000'.
            # This allows the browser to access MinIO directly from the host machine without SignatureDoesNotMatch errors.
            # We explicitly pass region to prevent Minio client from doing a network request to localhost:9000 to find the region
            external_client = Minio(
                "localhost:9000",
                access_key=self._access_key,
                secret_key=self._secret_key,
                secure=self._secure,
                region="us-east-1",
            )
            url = external_client.presigned_get_object(
                self._bucket, remote_path, expires=timedelta(seconds=expires_seconds)
            )
            return url
        except Exception as exc:
            logger.error(f"[MinIO] Failed to generate presigned URL for {remote_path}: {exc}")
            return ""


# ── AWS S3 Implementation ─────────────────────────────────────────────────────

class S3StorageClient(StorageClient):
    """
    Storage adapter for AWS S3.

    Environment variables (read by from_env()):
        AWS_S3_BUCKET          — bucket name (required)
        AWS_DEFAULT_REGION     — region (default: us-east-1)
        AWS_ACCESS_KEY_ID      — (optional; falls back to instance IAM role)
        AWS_SECRET_ACCESS_KEY  — (optional; falls back to instance IAM role)
        AWS_S3_ENDPOINT_URL    — (optional; for custom S3-compatible endpoints)
    """

    def __init__(
        self,
        bucket: str,
        region: str = "us-east-1",
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ):
        try:
            import boto3
            from botocore.exceptions import ClientError  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "boto3 package is required: pip install boto3"
            ) from exc

        import boto3

        self._bucket = bucket
        session_kwargs: dict = {"region_name": region}
        if access_key and secret_key:
            session_kwargs["aws_access_key_id"] = access_key
            session_kwargs["aws_secret_access_key"] = secret_key

        client_kwargs: dict = {}
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url

        self._s3 = boto3.client("s3", **session_kwargs, **client_kwargs)

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def from_env(cls) -> "S3StorageClient":
        """Construct from environment variables."""
        return cls(
            bucket=os.environ["AWS_S3_BUCKET"],
            region=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
            access_key=os.getenv("AWS_ACCESS_KEY_ID"),
            secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            endpoint_url=os.getenv("AWS_S3_ENDPOINT_URL"),
        )

    # ── StorageClient interface ───────────────────────────────────────────────

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        try:
            extra_args = {"ContentType": _guess_content_type(Path(local_path).suffix)}
            self._s3.upload_file(local_path, self._bucket, remote_path,
                                 ExtraArgs=extra_args)
            logger.info(f"[S3] Uploaded {local_path} → s3://{self._bucket}/{remote_path}")
            return True
        except Exception as exc:
            logger.error(f"[S3] upload_file failed ({remote_path}): {exc}")
            return False

    def upload_bytes(self, data: bytes, remote_path: str,
                     content_type: str = "application/octet-stream") -> bool:
        try:
            self._s3.put_object(
                Bucket=self._bucket,
                Key=remote_path,
                Body=data,
                ContentType=content_type,
            )
            logger.info(f"[S3] Uploaded {len(data)} bytes → s3://{self._bucket}/{remote_path}")
            return True
        except Exception as exc:
            logger.error(f"[S3] upload_bytes failed ({remote_path}): {exc}")
            return False

    def download_file(self, remote_path: str, local_path: str) -> bool:
        try:
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            self._s3.download_file(self._bucket, remote_path, local_path)
            logger.info(f"[S3] Downloaded s3://{self._bucket}/{remote_path} → {local_path}")
            return True
        except Exception as exc:
            logger.error(f"[S3] download_file failed ({remote_path}): {exc}")
            return False

    def delete_file(self, remote_path: str) -> bool:
        try:
            # S3 delete_object is idempotent — no error if key missing
            self._s3.delete_object(Bucket=self._bucket, Key=remote_path)
            logger.info(f"[S3] Deleted s3://{self._bucket}/{remote_path}")
            return True
        except Exception as exc:
            logger.error(f"[S3] delete_file failed ({remote_path}): {exc}")
            return False

    def file_exists(self, remote_path: str) -> bool:
        try:
            self._s3.head_object(Bucket=self._bucket, Key=remote_path)
            return True
        except Exception as exc:
            from botocore.exceptions import ClientError
            if isinstance(exc, ClientError) and exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return False
            logger.error(f"[S3] file_exists check failed ({remote_path}): {exc}")
            return False

    def get_presigned_url(self, remote_path: str, expires_seconds: int = 3600) -> str:
        """Generate a presigned GET URL for an S3 object."""
        try:
            url = self._s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": remote_path},
                ExpiresIn=expires_seconds
            )
            return url
        except Exception as exc:
            logger.error(f"[S3] Failed to generate presigned URL for {remote_path}: {exc}")
            return ""


# ── Factory ───────────────────────────────────────────────────────────────────

class StorageClientFactory:
    """
    Build the appropriate StorageClient from environment variables.

    STORAGE_BACKEND env var selects the implementation:
        "minio" (default) → MinioStorageClient.from_env()
        "s3"              → S3StorageClient.from_env()
    """

    @staticmethod
    def from_env() -> StorageClient:
        backend = os.getenv("STORAGE_BACKEND", "minio").lower()
        if backend == "s3" or os.getenv("AWS_S3_BUCKET"):
            return S3StorageClient.from_env()
        return MinioStorageClient.from_env()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _guess_content_type(suffix: str) -> str:
    """Return MIME type from file extension."""
    _MAP = {
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".avi": "video/x-msvideo",
        ".mkv": "video/x-matroska",
        ".webm": "video/webm",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".wav": "audio/wav",
        ".json": "application/json",
    }
    return _MAP.get(suffix.lower(), "application/octet-stream")
