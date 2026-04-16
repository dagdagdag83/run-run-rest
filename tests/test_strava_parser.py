import pytest

from src.features.strava.parser import transform_strava_activity


def test_transform_strava_activity_full():
    raw_data = {
        "id": 18123106292,
        "name": "Run 7000 Excite Live: Macao",
        "type": "Run",
        "total_elevation_gain": 0,
        "start_date_local": "2026-04-15T20:45:06Z",
        "distance": 5016.1,
        "moving_time": 2158,
        "average_speed": 2.324,
        "has_heartrate": True,
        "average_heartrate": 148.5,
        "max_heartrate": 170.0,
        "splits_metric": [
            {
                "split": 1,
                "average_speed": 2.34,
                "average_heartrate": 124.54778554778555
            },
            {
                "split": 2,
                "average_speed": 2.25,
                "average_heartrate": 157.289592760181
            }
        ]
    }

    result = transform_strava_activity(raw_data)

    assert result["id"] == 18123106292
    assert result["name"] == "Run 7000 Excite Live: Macao"
    assert result["type"] == "Run"
    assert result["total_elevation_gain"] == 0
    assert result["start_date_local"] == "2026-04-15"
    assert result["distance_km"] == 5.02
    assert result["moving_time"] == "35:58"
    assert result["average_pace_min_km"] == "7:10"
    assert result["average_heartrate"] == 148.5
    assert result["max_heartrate"] == 170.0

    splits = result.get("splits", [])
    assert len(splits) == 2
    assert splits[0]["km"] == 1
    assert splits[0]["average_pace_min_km"] == "7:07"   # 1000 / (2.34*60) -> 1000/140.4=7.12 -> 7:07
    assert splits[0]["average_heartrate"] == 124.54778554778555

    assert splits[1]["km"] == 2
    assert splits[1]["average_pace_min_km"] == "7:24"   # 1000 / (2.25*60) -> 1000/135=7.407... -> 7:24
    assert splits[1]["average_heartrate"] == 157.289592760181


def test_transform_strava_activity_handle_missing_and_zeroes():
    raw_data = {
        "id": 1,
        "name": "Slow walk",
        "type": "Walk",
        "total_elevation_gain": 10,
        "start_date_local": "2026-04-15T00:00:00Z",
        "distance": 0,
        "moving_time": 3661,
        "average_speed": 0,
        "has_heartrate": False
    }

    result = transform_strava_activity(raw_data)
    assert result["distance_km"] == 0.0
    assert result["moving_time"] == "1:01:01"
    assert result["average_pace_min_km"] == "0:00"
    assert result["average_heartrate"] is None
    assert result["max_heartrate"] is None
    assert "splits" in result and len(result["splits"]) == 0
