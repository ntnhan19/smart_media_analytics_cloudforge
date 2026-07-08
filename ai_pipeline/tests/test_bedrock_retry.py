"""
Test suite cho Bedrock Resilient Retry Strategy.

Hai điều quan trọng về thiết kế test này:

1. KHÔNG dùng stubber.calls — thuộc tính đó không tồn tại trong botocore.stub.Stubber.
   Thay vào đó, ta wrap client.invoke_model bằng MagicMock để đếm call_count,
   hoặc dùng stubber.assert_no_pending_responses() để xác nhận queue đã tiêu thụ hết.

2. Retry PHẢI được implement ở application layer (tenacity trong bedrock.py),
   KHÔNG dựa vào boto3 Config retry — vì Stubber bypass tầng HTTP nên boto3
   retry không có tác dụng khi test qua Stubber.
"""

import io
import json
import logging
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from botocore.stub import Stubber
from PIL import Image

from ai_pipeline.providers.bedrock import BedrockVisionProvider


class TestBedrockRetryStrategy(unittest.TestCase):

    def setUp(self):
        """Thiết lập môi trường test: ảnh giả và boto3 client không retry."""
        self.fake_image_path = Path("/tmp/fake_image.jpg")
        self.fake_image_path.parent.mkdir(exist_ok=True)
        img = Image.new("RGB", (100, 100), color="red")
        img.save(self.fake_image_path)

        # Client với max_attempts=1 (khớp với bedrock.py sau khi fix).
        # Stubber bypass HTTP nên boto3 retry config không ảnh hưởng gì ở đây,
        # nhưng giữ nhất quán với production code.
        no_retry_config = Config(
            retries={"max_attempts": 1, "mode": "standard"}
        )
        self.bedrock_runtime = boto3.client(
            "bedrock-runtime",
            region_name="us-east-1",
            config=no_retry_config,
        )

    def tearDown(self):
        if self.fake_image_path.exists():
            self.fake_image_path.unlink()

    # ------------------------------------------------------------------
    # Test 1: ThrottlingException → retry → thành công
    # ------------------------------------------------------------------

    def test_bedrock_vision_throttling_retry(self):
        """
        Test retry khi gặp ThrottlingException.
        Kịch bản: 3 lần ThrottlingException → lần thứ 4 thành công.

        Cách đếm số lần gọi:
          - Stubber queue tiêu thụ hết (assert_no_pending_responses) = 4 responses đã dùng.
          - invoke_model được wrap bằng MagicMock để lấy call_count chính xác.
        """
        stubber = Stubber(self.bedrock_runtime)

        successful_response = {
            "body": io.BytesIO(
                json.dumps({"content": [{"text": "A red square."}]}).encode("utf-8")
            ),
            "contentType": "application/json",
        }

        for _ in range(3):
            stubber.add_client_error(
                "invoke_model",
                service_error_code="ThrottlingException",
                http_status_code=429,
            )
        stubber.add_response("invoke_model", successful_response)

        # Wrap invoke_model để đếm call_count mà vẫn giữ behaviour của Stubber
        original_invoke = self.bedrock_runtime.invoke_model
        mock_invoke = MagicMock(side_effect=original_invoke)
        self.bedrock_runtime.invoke_model = mock_invoke

        with stubber:
            with patch("ai_pipeline.providers.bedrock._get_bedrock_client") as mock_get_client:
                mock_get_client.return_value = self.bedrock_runtime
                provider = BedrockVisionProvider(region_name="us-east-1")

                # Bắt log WARNING của ai_pipeline.providers.bedrock (tenacity gọi _log_retry_attempt)
                with self.assertLogs("ai_pipeline.providers.bedrock", level="WARNING") as log_cm:
                    result = provider.caption_keyframe(self.fake_image_path)

                self.assertEqual(result, "A red square.", "Caption phải trả về đúng text")

                # Kiểm tra log retry xuất hiện (DoD: "Attempt N failed with ... Retrying in ...")
                retry_logs = [
                    line for line in log_cm.output if "Retrying" in line
                ]
                self.assertGreaterEqual(
                    len(retry_logs), 1,
                    f"Phải có ít nhất 1 log retry. Logs nhận được: {log_cm.output}",
                )

            # Kiểm tra invoke_model được gọi đúng 4 lần (3 lỗi + 1 thành công)
            self.assertEqual(
                mock_invoke.call_count, 4,
                f"invoke_model phải được gọi 4 lần, thực tế: {mock_invoke.call_count}",
            )

            # Xác nhận Stubber queue đã tiêu thụ hết (không còn response pending nào)
            stubber.assert_no_pending_responses()

    # ------------------------------------------------------------------
    # Test 2: AccessDeniedException → KHÔNG retry
    # ------------------------------------------------------------------

    def test_bedrock_access_denied_no_retry(self):
        """
        Test lỗi 4xx (AccessDeniedException) KHÔNG được retry.
        Kịch bản: 1 lần AccessDeniedException → raise ngay, không thử lại.
        """
        stubber = Stubber(self.bedrock_runtime)
        stubber.add_client_error(
            "invoke_model",
            service_error_code="AccessDeniedException",
            http_status_code=403,
        )

        # Wrap invoke_model để đếm call_count
        original_invoke = self.bedrock_runtime.invoke_model
        mock_invoke = MagicMock(side_effect=original_invoke)
        self.bedrock_runtime.invoke_model = mock_invoke

        with stubber:
            with patch("ai_pipeline.providers.bedrock._get_bedrock_client") as mock_get_client:
                mock_get_client.return_value = self.bedrock_runtime
                provider = BedrockVisionProvider(region_name="us-east-1")

                with self.assertRaises(ClientError) as exc_cm:
                    provider.caption_keyframe(self.fake_image_path)

                # Đúng loại lỗi được raise ra
                self.assertEqual(
                    exc_cm.exception.response["Error"]["Code"],
                    "AccessDeniedException",
                )

            # invoke_model chỉ được gọi đúng 1 lần (không có retry)
            self.assertEqual(
                mock_invoke.call_count, 1,
                f"invoke_model phải được gọi đúng 1 lần với 4xx, thực tế: {mock_invoke.call_count}",
            )

    # ------------------------------------------------------------------
    # Test 3: Max retries vượt quá → raise lỗi cuối cùng
    # ------------------------------------------------------------------

    def test_bedrock_throttling_exceeds_max_retry(self):
        """
        Test khi số lỗi vượt quá max_attempts (4) → raise ThrottlingException.
        Kịch bản: 5 lần ThrottlingException liên tiếp → exception cuối được raise.
        """
        stubber = Stubber(self.bedrock_runtime)

        for _ in range(5):
            stubber.add_client_error(
                "invoke_model",
                service_error_code="ThrottlingException",
                http_status_code=429,
            )

        original_invoke = self.bedrock_runtime.invoke_model
        mock_invoke = MagicMock(side_effect=original_invoke)
        self.bedrock_runtime.invoke_model = mock_invoke

        with stubber:
            with patch("ai_pipeline.providers.bedrock._get_bedrock_client") as mock_get_client:
                mock_get_client.return_value = self.bedrock_runtime
                provider = BedrockVisionProvider(region_name="us-east-1")

                with self.assertRaises(ClientError) as exc_cm:
                    provider.caption_keyframe(self.fake_image_path)

                self.assertEqual(
                    exc_cm.exception.response["Error"]["Code"],
                    "ThrottlingException",
                    "Phải raise ThrottlingException sau khi hết retry",
                )

            # Đúng 4 lần (1 gốc + 3 retry), không gọi thêm
            self.assertEqual(
                mock_invoke.call_count, 4,
                f"invoke_model phải được gọi đúng 4 lần (stop_after_attempt=4), thực tế: {mock_invoke.call_count}",
            )


if __name__ == "__main__":
    unittest.main()