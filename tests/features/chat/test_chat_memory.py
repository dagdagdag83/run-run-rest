import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock
from src.features.chat.librarian.tools import (
    get_fuzzy_time_window,
    fetch_historical_chat,
    summarize_past_chat,
    prune_chat_context
)

def test_prune_chat_context():
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M")
    old = (now - timedelta(days=8)).strftime("%Y-%m-%d %H:%M")
    boundary = (now - timedelta(days=6, hours=23)).strftime("%Y-%m-%d %H:%M")
    
    messages = [
        {"role": "user", "content": f"[{old}] old user msg"},
        {"role": "assistant", "content": "old assistant msg"},
        {"role": "user", "content": f"[{boundary}] boundary msg"},
        {"role": "assistant", "content": "boundary assistant msg"},
        {"role": "user", "content": f"[{recent}] recent user msg"},
        {"role": "assistant", "content": "recent assistant msg"}
    ]
    
    pruned = prune_chat_context(messages, days=7)
    assert len(pruned) == 4
    assert pruned[0]["content"] == f"[{boundary}] boundary msg"
    assert "recent assistant msg" in pruned[-1]["content"]

def test_get_fuzzy_time_window():
    with patch("src.features.chat.librarian.tools.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 4, 17, tzinfo=timezone.utc)
        start, end = get_fuzzy_time_window(10)
        # target = 2026-04-07
        # start = target - 15 = 2026-03-23
        # end = target + 15 = 2026-04-22
        assert start == datetime(2026, 3, 23, tzinfo=timezone.utc)
        assert end == datetime(2026, 4, 22, tzinfo=timezone.utc)

@pytest.mark.asyncio
@patch("src.features.chat.librarian.tools.db")
async def test_fetch_historical_chat(mock_db):
    start = datetime(2026, 3, 1, tzinfo=timezone.utc)
    end = datetime(2026, 3, 31, tzinfo=timezone.utc)
    
    messages = [
        {"role": "user", "content": "[2026-02-15 10:00] user msg 1"}, # Before
        {"role": "assistant", "content": "assistant msg 1"}, # Before
        {"role": "user", "content": "[2026-03-15 10:00] user msg 2"}, # Inside
        {"role": "assistant", "content": "assistant msg 2"}, # Inside
        {"role": "user", "content": "[2026-04-05 10:00] user msg 3"} # After
    ]
    mock_db.get = AsyncMock(return_value={"messages": messages})
    
    result = await fetch_historical_chat("user_123", start, end)
    
    assert "user msg 2" in result
    assert "assistant msg 2" in result
    assert "user msg 1" not in result
    assert "user msg 3" not in result

@pytest.mark.asyncio
@patch("src.shared.dependencies.ai_client")
async def test_summarize_past_chat(mock_ai_client):
    mock_ai_client.aio.models.generate_content = AsyncMock()
    mock_response = AsyncMock()
    mock_response.text = "The user talked about running gels."
    mock_ai_client.aio.models.generate_content.return_value = mock_response
    
    raw_log = "User: [2026-03-15] I tried SiS gels.\nCoach: Nice."
    summary = await summarize_past_chat(raw_log, "gels")
    
    assert summary == "The user talked about running gels."
    mock_ai_client.aio.models.generate_content.assert_called_once()
    kwargs = mock_ai_client.aio.models.generate_content.call_args.kwargs
    assert kwargs["model"] == "gemini-3.1-flash-lite-preview"
