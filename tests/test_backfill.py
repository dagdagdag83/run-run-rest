import sys
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import Response, HTTPStatusError, Request

# Mock environment before importing
import os
os.environ["ENVIRONMENT"] = "local"

# We will test the core logic which we'll isolate in a function
# to avoid the argparse __name__ == '__main__' block during testing.

@pytest.fixture
def mock_db():
    with patch("scripts.backfill_strava.db") as mock:
        mock.get = AsyncMock()
        mock.put = AsyncMock()
        yield mock

@pytest.fixture
def mock_httpx():
    with patch("scripts.backfill_strava.httpx.AsyncClient") as client_mock:
        yield client_mock

@pytest.fixture
def mock_enrichments():
    with patch("scripts.backfill_strava.enrich_with_weather", new_callable=AsyncMock) as m_weather, \
         patch("scripts.backfill_strava.enrich_with_physiology", new_callable=AsyncMock) as m_physio, \
         patch("scripts.backfill_strava.enrich_with_scout_assessment", new_callable=AsyncMock) as m_scout, \
         patch("scripts.backfill_strava.transform_strava_activity") as m_transform, \
         patch("scripts.backfill_strava.get_valid_strava_token", new_callable=AsyncMock) as m_token:
         
         m_weather.return_value = {"temp": 20}
         m_physio.return_value = {"training_load": 100}
         m_scout.return_value = ["Good run"]
         m_transform.return_value = {"parsed": True, "type": "Run"}
         m_token.return_value = "fake_token"
         
         yield m_weather, m_physio, m_scout, m_transform, m_token

@pytest.mark.asyncio
async def test_backfill_strava_aborts_on_daily_limit(mock_db, mock_httpx, mock_enrichments):
    from scripts.backfill_strava import run_backfill
    
    # Mock token
    weather, physio, scout, transform, token = mock_enrichments
    token.return_value = "fake-token"
    
    # Setup HTTP client mock
    client_instance = mock_httpx.return_value.__aenter__.return_value
    
    # First request: get activities
    activities_response = Response(
        status_code=200, 
        json=[{"id": 101, "type": "Run"}]
    )
    activities_response.request = Request("GET", "https://mock")
    
    # Second request: get detailed activity, which hits daily limit
    detail_response = Response(
        status_code=200,
        json={"id": 101, "type": "Run", "detail": True},
        headers={
            "X-RateLimit-Usage": "10,1001", # 15-min usage, daily usage
            "X-RateLimit-Limit": "100,1000"
        }
    )
    detail_response.request = Request("GET", "https://mock")
    
    # Let side_effect return activities then detail
    client_instance.get.side_effect = [activities_response, detail_response]
    
    # Db get side effect - return None to pretend it does not exist
    mock_db.get.return_value = None
    
    with pytest.raises(SystemExit) as exc_info:
        await run_backfill(days_back=None)
        
    assert exc_info.value.code == 1
    # Check that it fetched the detail before exiting
    assert client_instance.get.call_count == 2
    
@pytest.mark.asyncio
async def test_backfill_strava_skips_existing_doc(mock_db, mock_httpx, mock_enrichments):
    from scripts.backfill_strava import run_backfill
    
    client_instance = mock_httpx.return_value.__aenter__.return_value
    activities_response = Response(
        status_code=200, 
        json=[{"id": 102, "type": "Run"}]
    )
    activities_response.request = Request("GET", "https://mock")
    
    empty_activities = Response(status_code=200, json=[])
    empty_activities.request = Request("GET", "https://mock")
    
    client_instance.get.side_effect = [activities_response, empty_activities]
    
    # Mock db to return True (document exists)
    mock_db.get.return_value = {"id": 102}
    
    await run_backfill(days_back=None)
    
    # It should only fetch activities list twice (page 1 and page 2), not the detail view
    assert client_instance.get.call_count == 2
    mock_db.put.assert_not_called()

@pytest.mark.asyncio
async def test_backfill_strava_sleeps_on_15min_limit(mock_db, mock_httpx, mock_enrichments):
    from scripts.backfill_strava import run_backfill
    weather, physio, scout, transform, token = mock_enrichments
    
    client_instance = mock_httpx.return_value.__aenter__.return_value
    activities_response = Response(
        status_code=200, 
        json=[{"id": 103, "type": "Run"}]
    )
    activities_response.request = Request("GET", "https://mock")
    
    detail_response = Response(
        status_code=200,
        json={"id": 103, "type": "Run"},
        headers={
            "X-RateLimit-Usage": "98,500", # Close to 15-min limit of 100
            "X-RateLimit-Limit": "100,1000"
        }
    )
    detail_response.request = Request("GET", "https://mock")
    
    # Add a third response to act as empty activities list to break the loop
    empty_activities = Response(status_code=200, json=[])
    empty_activities.request = Request("GET", "https://mock")
    
    client_instance.get.side_effect = [activities_response, detail_response, empty_activities]
    mock_db.get.return_value = None
    
    with patch("scripts.backfill_strava.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        await run_backfill(days_back=None)
        
        # Should have slept
        mock_sleep.assert_called_once_with(900) # Assuming 15 minutes sleep if limit is hit/close
        mock_db.put.assert_called()

