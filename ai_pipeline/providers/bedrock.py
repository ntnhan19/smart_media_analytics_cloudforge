import base64
import io
import json
import logging
import uuid
from pathlib import Path
from typing import List, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from PIL import Image
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
    before_sleep_log,
    RetryCallState,
)

from .base import TextEmbedder, VisionProvider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Retry helpers
# ---------------------------------------------------------------------------

# Các error code được phép retry (transient / throttle)
_RETRYABLE_CODES = {
    "ThrottlingException",
    "ServiceUnavailableException",
    "RequestTimeoutException",
    "InternalServerException",
    "ModelTimeoutException",
}

# HTTP status code được phép retry (5xx gateway errors)
_RETRYABLE_HTTP_STATUS = {502, 503, 504}


def _is_retryable(exc: BaseException) -> bool:
    """Trả về True nếu exception này nên được retry."""
    if not isinstance(exc, ClientError):
        return False
    error = exc.response.get("Error", {})
    code = error.get("Code", "")
    http_status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0)
    return code in _RETRYABLE_CODES or http_status in _RETRYABLE_HTTP_STATUS


def _log_retry_attempt(retry_state: RetryCallState) -> None:
    """Log rõ ràng mỗi lần retry theo yêu cầu DoD."""
    attempt = retry_state.attempt_number
    exc = retry_state.outcome.exception()
    if exc and isinstance(exc, ClientError):
        code = exc.response["Error"]["Code"]
        wait = getattr(retry_state.next_action, "sleep", None)
        wait_str = f"{wait:.1f}s" if wait is not None else "?"
        logger.warning(
            f"Attempt {attempt} failed with {code}. Retrying in {wait_str}..."
        )


# Decorator dùng lại cho cả Vision và Embedding
_bedrock_retry = retry(
    retry=retry_if_exception(_is_retryable),
    stop=stop_after_attempt(4),          # 1 lần gốc + 3 retry = 4 attempts
    wait=wait_exponential_jitter(
        initial=1, max=30, jitter=1      # backoff: 1s, 2s, 4s... + jitter
    ),
    before_sleep=_log_retry_attempt,
    reraise=True,
)


# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------

def _get_bedrock_client(region_name: Optional[str] = None):
    """
    Khởi tạo Bedrock Runtime client.

    Retry logic được xử lý hoàn toàn bởi tenacity ở tầng application
    nên boto3 chỉ cần max_attempts=1 để tránh chồng tầng retry.
    """
    no_retry_config = Config(
        retries={
            "max_attempts": 1,   # tắt boto3 retry, tenacity lo phần này
            "mode": "standard",
        }
    )
    return boto3.client(
        "bedrock-runtime",
        region_name=region_name,
        config=no_retry_config,
    )


# ---------------------------------------------------------------------------
# Image helper
# ---------------------------------------------------------------------------

def _image_to_base64(image_path: Path, max_size: int = 2048) -> str:
    """Convert image to base64 with optional resize."""
    image = Image.open(image_path).convert("RGB")

    width, height = image.size
    if max(width, height) > max_size:
        scale = max_size / max(width, height)
        image = image.resize(
            (int(width * scale), int(height * scale)),
            Image.Resampling.LANCZOS,
        )

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


# ---------------------------------------------------------------------------
# Vision Provider
# ---------------------------------------------------------------------------

class BedrockVisionProvider(VisionProvider):
    """AWS Bedrock Vision Provider sử dụng Claude 3.5 Sonnet."""

    def __init__(self, model_id: Optional[str] = None, region_name: Optional[str] = None):
        self.model_id = model_id or "anthropic.claude-3-5-sonnet-20240620-v1:0"
        self.region_name = region_name
        self.client = _get_bedrock_client(region_name)

    def caption_keyframe(
        self,
        image_path: Path,
        prompt: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> str:
        """Tạo caption cho keyframe với retry support."""
        req_id = request_id or str(uuid.uuid4())

        prompt = prompt or (
            "Describe this video keyframe for semantic search. "
            "Mention the scene type, main subjects, visible objects, action, "
            "location cues, lighting, and mood. Keep it concise."
        )

        image_b64 = _image_to_base64(image_path)

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 512,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_b64,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        }

        @_bedrock_retry
        def _invoke() -> str:
            try:
                response = self.client.invoke_model(
                    body=json.dumps(body),
                    modelId=self.model_id,
                )
                response_body = json.loads(response["body"].read())
                return response_body["content"][0]["text"].strip()
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                logger.error(
                    f"Bedrock Vision failed (request_id: {req_id}, code: {error_code})"
                )
                raise

        return _invoke()


# ---------------------------------------------------------------------------
# Text Embedder
# ---------------------------------------------------------------------------

class BedrockTextEmbedder(TextEmbedder):
    """AWS Bedrock Text Embedding Provider sử dụng Titan Embeddings v2."""

    def __init__(
        self,
        model_id: Optional[str] = None,
        region_name: Optional[str] = None,
        embedding_dim: int = 1024,
    ):
        self.model_id = model_id or "amazon.titan-embed-text-v2:0"
        self.region_name = region_name
        self.embedding_dim = embedding_dim
        self.client = _get_bedrock_client(region_name)

    def embed_text(self, text: str, request_id: Optional[str] = None) -> List[float]:
        """Tạo embedding cho một đoạn văn bản."""
        return self.embed_texts([text], request_id)[0]

    def embed_texts(
        self,
        texts: List[str],
        request_id: Optional[str] = None,
    ) -> List[List[float]]:
        """Tạo embedding cho nhiều văn bản."""
        req_id = request_id or str(uuid.uuid4())

        if not texts:
            return []

        @_bedrock_retry
        def _invoke_single(text: str) -> List[float]:
            try:
                body = json.dumps({
                    "inputText": text,
                    "dimensions": self.embedding_dim,
                    "normalize": True,
                })
                response = self.client.invoke_model(
                    body=body,
                    modelId=self.model_id,
                )
                response_body = json.loads(response["body"].read())
                return response_body["embedding"]
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                logger.error(
                    f"Bedrock Embedding failed (request_id: {req_id}, code: {error_code})"
                )
                raise

        return [_invoke_single(text) for text in texts]