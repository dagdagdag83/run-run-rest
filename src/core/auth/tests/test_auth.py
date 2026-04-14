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
async def test_root_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

@pytest.mark.asyncio
async def test_api_me_unauth():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.skip(reason="Requires fetching real discovery URL via network")
@pytest.mark.asyncio
async def test_login_redirect():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/login")
    assert response.status_code in [302, 303]
