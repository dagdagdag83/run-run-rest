import pytest
from httpx import AsyncClient, ASGITransport
import os
os.environ['SESSION_SECRET_KEY'] = 'test-secret'
os.environ['ZITADEL_DISCOVERY_URL'] = 'https://test/.well-known'
os.environ['ZITADEL_CLIENT_ID'] = 'test'
os.environ['ZITADEL_CLIENT_SECRET'] = 'test'
from main import app

@pytest.mark.asyncio
async def test_webhook_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/webhook", json={"data": "test"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "webhook received"}

@pytest.mark.asyncio
async def test_chat_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/chat", json={"message": "hello"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "response": "mock response"}

@pytest.mark.asyncio
async def test_root_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "chat-log" in response.text

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

