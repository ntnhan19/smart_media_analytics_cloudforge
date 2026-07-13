import json
import logging
import asyncio
from typing import Dict, List
from fastapi import WebSocket
import redis.asyncio as redis
from config import settings

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Maps job_id to a list of active websocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.redis_client = redis.from_url(
            settings.REDIS_URL, 
            decode_responses=True,
            socket_connect_timeout=5
        )
        self.pubsub_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
            # Start a Redis pubsub listener for this job if not already running
            self._start_redis_listener(job_id)
            
        self.active_connections[job_id].append(websocket)
        logger.info(f"WebSocket connected for job_id: {job_id}")

    def _start_redis_listener(self, job_id: str):
        if job_id not in self.pubsub_tasks:
            task = asyncio.create_task(self._listen_to_redis(job_id))
            self.pubsub_tasks[job_id] = task

    async def _listen_to_redis(self, job_id: str):
        pubsub = self.redis_client.pubsub()
        channel_name = f"job_{job_id}"
        await pubsub.subscribe(channel_name)
        logger.info(f"Subscribed to Redis channel: {channel_name}")
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    payload = message["data"]
                    # Broadcast to all local websockets
                    await self._broadcast_to_local_connections(job_id, payload)
        except Exception as e:
            logger.error(f"Redis listener error for {job_id}: {e}")
        finally:
            await pubsub.unsubscribe(channel_name)

    async def _broadcast_to_local_connections(self, job_id: str, message: str):
        if job_id in self.active_connections:
            # We must iterate over a copy or handle disconnections carefully
            for connection in list(self.active_connections[job_id]):
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Failed to send message to websocket for job_id {job_id}: {e}")
                    self.disconnect(connection, job_id)

    def disconnect(self, websocket: WebSocket, job_id: str):
        if job_id in self.active_connections:
            if websocket in self.active_connections[job_id]:
                self.active_connections[job_id].remove(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
                # Stop Redis listener
                if job_id in self.pubsub_tasks:
                    self.pubsub_tasks[job_id].cancel()
                    del self.pubsub_tasks[job_id]
        logger.info(f"WebSocket disconnected for job_id: {job_id}")

    async def publish_progress(self, job_id: str, payload: dict):
        """Used by the backend to publish progress to Redis, which the listener will pick up."""
        channel_name = f"job_{job_id}"
        message = json.dumps(payload)
        await self.redis_client.publish(channel_name, message)

manager = ConnectionManager()
