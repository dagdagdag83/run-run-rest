import pytest
from unittest.mock import patch, AsyncMock
from src.features.strava.weather import enrich_with_weather
import httpx

@pytest.fixture
def sample_activity():
    return {
        "start_date": "2024-05-14T14:52:00Z",
        "start_latlng": [48.8566, 2.3522]
    }

@pytest.fixture
def mock_open_meteo_response():
    return {
        "hourly": {
            "time": [
                "2024-05-14T13:00",
                "2024-05-14T14:00",
                "2024-05-14T15:00"
            ],
            "temperature_2m": [15.1, 16.5, 16.0],
            "weather_code": [0, 3, 61],
            "wind_speed_10m": [10.2, 12.5, 14.0]
        }
    }

@pytest.mark.asyncio
@patch("src.features.strava.weather.httpx.AsyncClient")
async def test_weather_success(mock_client_cls, sample_activity, mock_open_meteo_response):
    mock_instance = AsyncMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_instance
    
    from unittest.mock import Mock
    mock_response = Mock()
    mock_response.json.return_value = mock_open_meteo_response
    mock_response.raise_for_status = Mock()
    mock_instance.get.return_value = mock_response

    result = await enrich_with_weather(sample_activity)

    # 14:52 translates to 14:00 in our matching logic
    assert result is not None
    assert result["temp_c"] == 16.5
    assert result["condition"] == "Overcast"
    assert result["wind_kph"] == 12.5
    assert result["likely_indoors"] is False

    # Check that client.get was called
    mock_instance.get.assert_called_once()
    call_args = mock_instance.get.call_args
    assert call_args.kwargs["params"]["latitude"] == 48.8566
    assert call_args.kwargs["params"]["longitude"] == 2.3522

@pytest.mark.asyncio
@patch("src.features.strava.weather.httpx.AsyncClient")
async def test_weather_empty_latlng(mock_client_cls, mock_open_meteo_response):
    mock_instance = AsyncMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_instance
    
    from unittest.mock import Mock
    mock_response = Mock()
    mock_response.json.return_value = mock_open_meteo_response
    mock_response.raise_for_status = Mock()
    mock_instance.get.return_value = mock_response

    # Missing latlng
    activity = {
        "start_date": "2024-05-14T14:52:00Z"
    }
    result = await enrich_with_weather(activity)

    assert result is not None
    assert result["likely_indoors"] is True
    mock_instance.get.assert_called_once()
    call_args = mock_instance.get.call_args
    # Falls back to Trondheim
    assert call_args.kwargs["params"]["latitude"] == 63.43
    assert call_args.kwargs["params"]["longitude"] == 10.39

@pytest.mark.asyncio
@patch("src.features.strava.weather.httpx.AsyncClient")
async def test_weather_http_error(mock_client_cls, sample_activity):
    mock_instance = AsyncMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_instance
    
    mock_instance.get.side_effect = httpx.RequestError("Network timeout")

    result = await enrich_with_weather(sample_activity)

    # Should gracefully fail and return None
    assert result is None

@pytest.mark.parametrize("latlng,trainer_flag,expected_indoors", [
    ([48.8, 2.3], False, False),
    ([48.8, 2.3], True, True),
    ([], False, True),
    (None, False, True),
    (None, True, True),
])
@pytest.mark.asyncio
@patch("src.features.strava.weather.httpx.AsyncClient")
async def test_weather_likely_indoors_variations(mock_client_cls, latlng, trainer_flag, expected_indoors, mock_open_meteo_response):
    mock_instance = AsyncMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_instance
    
    from unittest.mock import Mock
    mock_response = Mock()
    mock_response.json.return_value = mock_open_meteo_response
    mock_response.raise_for_status = Mock()
    mock_instance.get.return_value = mock_response

    activity = {
        "start_date": "2024-05-14T14:52:00Z",
        "trainer": trainer_flag
    }
    if latlng is not None:
        activity["start_latlng"] = latlng

    result = await enrich_with_weather(activity)
    
    assert result is not None
    assert result["likely_indoors"] is expected_indoors
