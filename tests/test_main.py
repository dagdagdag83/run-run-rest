import pytest
from httpx import AsyncClient, ASGITransport
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
