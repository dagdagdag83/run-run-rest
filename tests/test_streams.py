import pytest
import base64
from unittest.mock import AsyncMock, patch, MagicMock
from src.features.strava.visualizer.streams import generate_stream_chart_base64, fetch_activity_streams

@pytest.mark.asyncio
async def test_fetch_activity_streams_success(mocker):
    # Mock token
    mocker.patch("src.features.strava.visualizer.streams.get_valid_strava_token", return_value="fake_token")
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "time": {"data": [0, 1, 2]},
        "heartrate": {"data": [140, 145, 150]},
        "velocity_smooth": {"data": [3.5, 3.6, 3.4]}
    }
    
    mock_client_instance = AsyncMock()
    mock_client_instance.get.return_value = mock_response
    
    # Mock httpx.AsyncClient context manager
    mock_client_cls = mocker.patch("src.features.strava.visualizer.streams.httpx.AsyncClient")
    mock_client_cls.return_value.__aenter__.return_value = mock_client_instance
    
    result = await fetch_activity_streams(12345, "user_1")
    
    assert result is not None
    assert "time" in result
    assert result["time"]["data"] == [0, 1, 2]

def test_generate_stream_chart_base64():
    streams = {
        "time": {"data": [0, 60, 120]}, # 2 mins
        "heartrate": {"data": [140, 145, 150]},
        "velocity_smooth": {"data": [3.33, 4.0, 5.0]} # Pace min/km equivalent: 5.0, 4.16, 3.33
    }
    
    b64_str = generate_stream_chart_base64(streams)
    
    assert isinstance(b64_str, str)
    assert len(b64_str) > 100
    
    # Validate it's a valid base64 decoder
    img_bytes = base64.b64decode(b64_str)
    assert img_bytes.startswith(b'\x89PNG\r\n\x1a\n') # PNG header

def test_generate_stream_chart_base64_stopped():
    streams = {
        "time": {"data": [0, 60, 120]},
        "heartrate": {"data": [140, 145, 150]},
        "velocity_smooth": {"data": [3.33, 0.0, 5.0]} # Missing/stopped pace shouldn't crash
    }
    b64_str = generate_stream_chart_base64(streams)
    assert isinstance(b64_str, str)
    assert len(b64_str) > 100

def test_generate_stream_chart_missing_time():
    streams = {
        "heartrate": {"data": [140, 145, 150]},
    }
    with pytest.raises(ValueError):
        generate_stream_chart_base64(streams)
