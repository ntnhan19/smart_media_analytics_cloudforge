import logging
import os
from minio import Minio

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        # MVP fallback - in the future this should read from config.py
        # For now, it just mocks or generates local streaming URLs
        pass

    async def delete_asset_files(self, asset_id: str, video_key: str, keyframe_keys: list[str]):
        """
        Delete original video, proxy and thumbnails on S3/MinIO
        """
        logger.info(f"StorageService: Deleting files for asset {asset_id}")
        # In a real S3 setup:
        # self.client.remove_object(self.bucket_name, video_key)
        # for k in keyframe_keys: self.client.remove_object(self.bucket_name, k)
        return True

    def get_stream_url(self, file_path: str) -> str:
        """
        Decides stream link: local backend link or S3 Presigned URL.
        For MVP, returns a local static route format.
        """
        # If we had S3 config, we would do:
        # return self.client.presigned_get_object(self.bucket_name, file_path)
        
        # Local fallback format: /api/v1/media/serve?path=xyz
        return f"http://localhost:8000/api/v1/media/serve?path={file_path}"

storage_service = StorageService()
