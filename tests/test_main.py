import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
import os
os.environ['SESSION_SECRET_KEY'] = 'test-secret'
os.environ['ZITADEL_DISCOVERY_URL'] = 'https://test/.well-known'
os.environ['ZITADEL_CLIENT_ID'] = 'test'
os.environ['ZITADEL_CLIENT_SECRET'] = 'test'

# Prevent any real external connections during FastAPI initialization
with patch('google.auth.default', side_effect=Exception('Mocked for tests')), \
     patch('google.genai.Client', side_effect=Exception('Mocked for tests')):
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
async def test_chat_endpoint_no_token():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/chat", json={"message": "hello"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

from src.shared.dependencies import get_current_user

@pytest.mark.asyncio
@patch("src.features.chat.router.ai_client", None)
async def test_chat_endpoint_success():
    async def override_get_current_user():
        return {"name": "Test User", "sub": "user_123"}

    app.dependency_overrides[get_current_user] = override_get_current_user
    
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post("/chat", json={"message": "hello"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "messages" in data
        assert len(data["messages"]) >= 2
        assert data["messages"][-2]["role"] == "user"
        assert data["messages"][-2]["content"].endswith("hello")
        assert data["messages"][-1]["role"] == "assistant"
        assert "unavailable" in data["messages"][-1]["content"]
        assert data["context_loaded"] is True
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
@patch("src.features.chat.router.db")
async def test_chat_anchor_prompt_injection(mock_db):
    mock_db.get = AsyncMock(return_value=None)
    mock_db.put = AsyncMock()
    
    # We patch ai_client in the router module with an AsyncMock so we can inspect genai_contents
    mock_ai_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.function_calls = []
    mock_response.text = "Hello from mocked AI!"
    mock_ai_client.aio.models.generate_content.return_value = mock_response

    async def override_get_current_user():
        return {"name": "Test User", "sub": "user_123"}

    app.dependency_overrides[get_current_user] = override_get_current_user
    
    with patch("src.features.chat.router.ai_client", mock_ai_client):
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.post("/chat", json={"message": "how do I bake a cake?"})
            
            assert response.status_code == 200
            data = response.json()
            
            # The returned message array should be pure (no Anchor Prompt)
            user_msg = data["messages"][-2]
            assert user_msg["role"] == "user"
            assert "how do I bake a cake?" in user_msg["content"]
            assert "SYSTEM DIRECTIVE" not in user_msg["content"], "Anchor Prompt leaked into pure messages array!"
            
            # The call to the mocked AI client should contain the Anchor Prompt
            mock_ai_client.aio.models.generate_content.assert_called_once()
            kwargs = mock_ai_client.aio.models.generate_content.call_args.kwargs
            
            # Contents should be an array of types.Content
            genai_contents = kwargs.get("contents")
            assert genai_contents is not None
            
            # The last Content part should have the anchor prompt text
            last_content = genai_contents[-1]
            assert getattr(last_content, "role", None) == "user"
            
            text_part = last_content.parts[0].text
            assert "SYSTEM DIRECTIVE: You are the athlete's Fitness Coach." in text_part, "Anchor prompt not injected before LLM text!"
            
        finally:
            app.dependency_overrides.clear()

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

