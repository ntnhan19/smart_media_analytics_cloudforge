import asyncio
import boto3
import json
import logging
import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import settings
from services.ingest_service import run_ingest_pipeline, run_ingest_pipeline_with_cleanup
from schemas.ingest import IngestOptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sqs_worker")

async def poll_sqs():
    sqs = boto3.client('sqs', region_name=settings.AWS_REGION)
    queue_url = settings.SQS_QUEUE_URL

    if not queue_url:
        logger.error("SQS_QUEUE_URL is not set!")
        return

    logger.info(f"Started polling SQS queue: {queue_url}")

    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20
            )

            messages = response.get('Messages', [])
            for message in messages:
                receipt_handle = message['ReceiptHandle']
                body = json.loads(message['Body'])
                
                job_id = body.get('job_id')
                source_path = body.get('source_path')
                options_dict = body.get('options', {})
                is_upload = body.get('is_upload', False)
                is_retry = body.get('is_retry', False)
                
                logger.info(f"Received job {job_id} from SQS")
                
                options = IngestOptions(**options_dict)
                
                try:
                    if is_upload:
                        await run_ingest_pipeline_with_cleanup(job_id, source_path, options)
                    else:
                        await run_ingest_pipeline(job_id, source_path, options, is_retry=is_retry)
                        
                    # Delete message on success
                    sqs.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=receipt_handle
                    )
                    logger.info(f"Successfully processed and deleted message for job {job_id}")
                except Exception as e:
                    logger.error(f"Error processing job {job_id}: {e}")
                    # Don't delete message so it goes to DLQ (after visibility timeout/retries)
                    
        except Exception as e:
            logger.error(f"Error receiving from SQS: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(poll_sqs())
