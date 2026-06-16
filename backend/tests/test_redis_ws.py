import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from core.websocket_manager import ConnectionManager

@pytest.mark.asyncio
async def test_redis_pubsub_publish():
    with patch("core.websocket_manager.redis.from_url") as mock_redis:
        mock_client = AsyncMock()
        mock_redis.return_value = mock_client
        
        manager = ConnectionManager()
        
        await manager.publish_progress("123", {"status": "processing"})
        
        mock_client.publish.assert_awaited_once_with("job_123", '{"status": "processing"}')

@pytest.mark.asyncio
async def test_websocket_connect_starts_listener():
    with patch("core.websocket_manager.redis.from_url") as mock_redis:
        manager = ConnectionManager()
        manager._start_redis_listener = MagicMock()
        
        mock_ws = AsyncMock()
        await manager.connect(mock_ws, "456")
        
        manager._start_redis_listener.assert_called_once_with("456")
        assert "456" in manager.active_connections
        assert mock_ws in manager.active_connections["456"]

@pytest.mark.asyncio
async def test_websocket_disconnect_stops_listener():
    with patch("core.websocket_manager.redis.from_url"):
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        
        # Simulate connected state
        manager.active_connections["789"] = [mock_ws]
        mock_task = MagicMock()
        manager.pubsub_tasks["789"] = mock_task
        
        manager.disconnect(mock_ws, "789")
        
        assert "789" not in manager.active_connections
        assert "789" not in manager.pubsub_tasks
        mock_task.cancel.assert_called_once()
