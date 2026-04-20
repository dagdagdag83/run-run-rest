import pytest
from unittest.mock import AsyncMock, patch
from src.features.chat.memory.utils import DistanceCategory, parse_time_to_seconds

def test_parse_time_to_seconds_valid():
    assert parse_time_to_seconds("24:30") == 24 * 60 + 30
    assert parse_time_to_seconds("1:45:15") == 3600 + 45 * 60 + 15
    assert parse_time_to_seconds("0:10:00") == 10 * 60
    assert parse_time_to_seconds("45:00") == 45 * 60
    assert parse_time_to_seconds("59") == 59
    assert parse_time_to_seconds(" 20:00 ") == 1200

def test_parse_time_to_seconds_invalid():
    with pytest.raises(ValueError):
        parse_time_to_seconds("abc")
    with pytest.raises(ValueError):
        parse_time_to_seconds("1:2:3:4")
    with pytest.raises(ValueError):
        parse_time_to_seconds("")

@pytest.mark.asyncio
@patch("src.features.chat.memory.tools.db")
async def test_log_personal_best_faster(mock_db):
    from src.features.chat.memory.tools import log_personal_best
    
    # Mock current PB as slower (e.g. 25:00)
    mock_db.list = AsyncMock(return_value=[
        {"distance_category": DistanceCategory.FIVE_K, "time_string": "25:00", "time_seconds": 1500, "activity_id": "123"}
    ])
    mock_db.put = AsyncMock()

    # Log faster PB (24:30)
    response = await log_personal_best("user_123", DistanceCategory.FIVE_K, "24:30", "456")
    
    assert response["status"] == "success"
    mock_db.put.assert_called_once()
    
@pytest.mark.asyncio
@patch("src.features.chat.memory.tools.db")
async def test_log_personal_best_slower(mock_db):
    from src.features.chat.memory.tools import log_personal_best
    
    # Mock current PB as faster (e.g. 24:00)
    mock_db.list = AsyncMock(return_value=[
        {"distance_category": DistanceCategory.FIVE_K, "time_string": "24:00", "time_seconds": 1440, "activity_id": "123"}
    ])
    mock_db.put = AsyncMock()

    # Log slower time (24:30)
    response = await log_personal_best("user_123", DistanceCategory.FIVE_K, "24:30", "456")
    
    assert "rejected" in response["status"]
    assert "24:00" in response["message"]
    mock_db.put.assert_not_called()

@pytest.mark.asyncio
@patch("src.features.chat.memory.tools.db")
async def test_log_personal_best_first_time(mock_db):
    from src.features.chat.memory.tools import log_personal_best
    
    # Mock empty collection
    mock_db.list = AsyncMock(return_value=[])
    mock_db.put = AsyncMock()

    # Log PB 
    response = await log_personal_best("user_123", DistanceCategory.TEN_K, "40:00", "789")
    
    assert response["status"] == "success"
    mock_db.put.assert_called_once()

@pytest.mark.asyncio
@patch("src.features.chat.memory.tools.db")
async def test_get_personal_best_current(mock_db):
    from src.features.chat.memory.tools import get_personal_best
    
    mock_db.list = AsyncMock(return_value=[
        {"distance_category": DistanceCategory.FIVE_K, "time_string": "24:00", "time_seconds": 1440, "activity_id": "123", "created_at": "timestamp"}
    ])

    response = await get_personal_best("user_123", DistanceCategory.FIVE_K, include_history=False)
    
    assert response["status"] == "success"
    assert len(response["personal_bests"]) == 1
    mock_db.list.assert_called_with("users/user_123/personal_bests")
