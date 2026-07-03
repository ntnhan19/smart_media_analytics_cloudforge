import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_invalid_extension_upload():
    # Attempt to upload a .exe file
    files = {"file": ("malicious.exe", b"fake exe content", "application/x-msdownload")}
    response = client.post("/api/v1/ingest/upload", files=files)
    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"]

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
    response = client.get("/api/v1/search/tags")
    # Even if DB is empty, it should return 200 and a list
    assert response.status_code == 200
    assert isinstance(response.json(), list)
