import logging
import os
from .storage_client import StorageClientFactory

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        try:
            self.client = StorageClientFactory.from_env()
            logger.info("StorageService: Initialized storage client successfully.")
        except Exception as e:
            logger.warning(f"StorageService: Failed to initialize storage client (using fallback): {e}")
            self.client = None

    async def delete_asset_files(self, asset_id: str, video_key: str, keyframe_keys: list[str]):
        """
        Delete original video, proxy and thumbnails on S3/MinIO
        """
        logger.info(f"StorageService: Deleting files for asset {asset_id}")
        if not self.client:
            return True
            
        try:
            # Delete original video
            if video_key:
                self.client.delete_file(video_key)
            # Delete thumbnails
            for k in keyframe_keys:
                if k:
                    self.client.delete_file(k)
            return True
        except Exception as e:
            logger.error(f"StorageService: Error deleting files: {e}")
            return False

    def get_stream_url(self, file_path: str) -> str:
        """
        Decides stream link: local backend link or S3 Presigned URL.
        """
        if self.client and hasattr(self.client, 'get_presigned_url'):
            url = self.client.get_presigned_url(file_path)
            if url:
                return url
        
        # Local fallback format: /api/v1/media/serve?path=xyz
        return f"http://localhost:8000/api/v1/media/serve?path={file_path}"

storage_service = StorageService()
