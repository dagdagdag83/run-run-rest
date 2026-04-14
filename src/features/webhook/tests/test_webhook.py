import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
import os

os.environ['SESSION_SECRET_KEY'] = 'test-secret'
os.environ['ZITADEL_DISCOVERY_URL'] = 'https://test/.well-known'
os.environ['ZITADEL_CLIENT_ID'] = 'test'
os.environ['ZITADEL_CLIENT_SECRET'] = 'test'

with patch('google.auth.default', side_effect=Exception('Mocked for tests')), \
     patch('google.genai.Client', side_effect=Exception('Mocked for tests')):
    from src.main import app

@pytest.mark.asyncio
async def test_webhook_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/webhook", json={"data": "test"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "webhook received"}
