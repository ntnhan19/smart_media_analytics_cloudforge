import pytest
import sys
import os

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_max_file_size():
    from config import settings
    from database import get_db
    
    # Mock Database session để bypass bước lưu metadata
    async def override_get_db():
        class MockSession:
            def add(self, *args, **kwargs): pass
            async def commit(self): pass
            async def refresh(self, obj, *args, **kwargs): pass
            async def execute(self, *args, **kwargs): 
                class MockResult:
                    def scalars(self): return []
                return MockResult()
            async def close(self): pass
        yield MockSession()
        
    app.dependency_overrides[get_db] = override_get_db
    
    # Lưu lại size cũ
    original_size = settings.MAX_UPLOAD_SIZE_BYTES
    
    try:
        # Ép size tối đa xuống chỉ còn 10 Bytes
        settings.MAX_UPLOAD_SIZE_BYTES = 10 
        
        # Tạo một file giả nặng 20 Bytes (lớn hơn mức cho phép)
        files = {"file": ("test.mp4", b"a" * 20, "video/mp4")}
        
        # Hàm test này chạy TRƯỚC test_rate_limiting nên chưa bị dính 429
        response = client.post("/api/v1/ingest/upload", files=files)
        
        # Phải trả về lỗi 413 Payload Too Large
        assert response.status_code == 413
        assert "Payload Too Large" in response.json()["detail"]
    finally:
        # Phục hồi lại size cũ để không ảnh hưởng các test khác
        settings.MAX_UPLOAD_SIZE_BYTES = original_size
        app.dependency_overrides.pop(get_db, None)

def test_invalid_extension_upload():
    # Attempt to upload a .exe file
    files = {"file": ("malicious.exe", b"fake exe content", "application/x-msdownload")}
    response = client.post("/api/v1/ingest/upload", files=files)
    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"]

def test_security_headers():
    # Gọi API health check đơn giản để kiểm tra Headers
    response = client.get("/health")
    headers = response.headers
    
    assert "x-content-type-options" in headers
    assert headers["x-content-type-options"] == "nosniff"
    assert "x-frame-options" in headers
    assert headers["x-frame-options"] == "DENY"
    assert "strict-transport-security" in headers

def test_rate_limiting():
    # Hit the upload endpoint multiple times to trigger rate limit (3/minute)
    files = {"file": ("test.mp4", b"dummy content", "video/mp4")}
    
    # Send 4 requests (4th should fail with 429)
    for _ in range(3):
        response = client.post("/api/v1/ingest/upload", files=files)
        # It might fail with DB error since it's a test client without mocked DB, but we only care about 429
        
    response = client.post("/api/v1/ingest/upload", files=files)
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.text

def test_tags_api_structure():
    from database import get_db
    
    # Mock Database session để không bị lỗi 500 khi không có kết nối DB
    async def override_get_db():
        class MockResult:
            def scalars(self): return []
        class MockSession:
            async def execute(self, *args, **kwargs): return MockResult()
            async def close(self): pass
        yield MockSession()

    app.dependency_overrides[get_db] = override_get_db
    
    try:
        response = client.get("/api/v1/search/tags")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        app.dependency_overrides.pop(get_db, None)
