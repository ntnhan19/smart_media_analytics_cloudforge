import boto3
import json
import logging
from config import settings

logger = logging.getLogger(__name__)

def get_sqs_client():
    if not settings.SQS_QUEUE_URL:
        return None
    return boto3.client('sqs', region_name=settings.AWS_REGION)

async def publish_ingest_job(job_id_str: str, source_path: str, options, is_upload: bool = False, is_retry: bool = False):
    """
    Push message to SQS instead of running it locally.
    """
    sqs = get_sqs_client()
    if not sqs or not settings.SQS_QUEUE_URL:
        logger.error("SQS_QUEUE_URL is not configured. Cannot publish job.")
        return False
        
    # options param is a Pydantic model (IngestOptions), convert to dict
    options_dict = options.dict() if hasattr(options, 'dict') else options
        
    message_body = {
        "job_id": job_id_str,
        "source_path": source_path,
        "options": options_dict,
        "is_upload": is_upload,
        "is_retry": is_retry
    }
    
    try:
        response = sqs.send_message(
            QueueUrl=settings.SQS_QUEUE_URL,
            MessageBody=json.dumps(message_body)
        )
        logger.info(f"Successfully published job {job_id_str} to SQS. MessageId: {response.get('MessageId')}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish job {job_id_str} to SQS: {e}")
        return False
