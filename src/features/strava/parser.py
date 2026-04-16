from typing import Dict, Any, Optional

def format_time(seconds: int) -> str:
    """Formats seconds into MM:SS or HH:MM:SS."""
    if seconds is None:
        return "0:00"
    minutes, remaining_seconds = divmod(seconds, 60)
    if minutes >= 60:
        hours, minutes = divmod(minutes, 60)
        return f"{hours}:{minutes:02d}:{remaining_seconds:02d}"
    return f"{minutes}:{remaining_seconds:02d}"

def calculate_pace(speed_m_s: float) -> str:
    """Convers speed in m/s to pace in min/km (format M:SS)."""
    if speed_m_s is None or speed_m_s <= 0:
        return "0:00"
    seconds_per_km = 1000 / speed_m_s
    minutes = int(seconds_per_km // 60)
    seconds = int(round(seconds_per_km % 60))
    if seconds == 60:
        minutes += 1
        seconds = 0
    return f"{minutes}:{seconds:02d}"

def transform_strava_activity(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parses raw strava webhook payload into a flattened/simplified structure."""
    
    start_date_local = raw_data.get("start_date_local")
    parsed_date = start_date_local.split("T")[0] if start_date_local else None

    distance = raw_data.get("distance", 0)
    distance_km = round(distance / 1000.0, 2) if distance else 0.0

    moving_time_sec = raw_data.get("moving_time", 0)
    moving_time_str = format_time(moving_time_sec)

    avg_speed = raw_data.get("average_speed", 0)
    pace_str = calculate_pace(avg_speed)

    has_hr = raw_data.get("has_heartrate", False)
    avg_hr = raw_data.get("average_heartrate") if has_hr else None
    max_hr = raw_data.get("max_heartrate") if has_hr else None

    # Parse splits
    splits_metric = raw_data.get("splits_metric", [])
    parsed_splits = []
    for split in splits_metric:
        parsed_splits.append({
            "km": split.get("split"),
            "average_pace_min_km": calculate_pace(split.get("average_speed")),
            "average_heartrate": split.get("average_heartrate")
        })

    device_name = raw_data.get("device_name")
    sport_type = raw_data.get("sport_type") or raw_data.get("type", "Unknown")

    return {
        "id": raw_data.get("id"),
        "name": raw_data.get("name"),
        "type": raw_data.get("type"),
        "sport_type": sport_type,
        "device_name": device_name,
        "total_elevation_gain": raw_data.get("total_elevation_gain"),
        "start_date_local": parsed_date,
        "distance_km": distance_km,
        "moving_time": moving_time_str,
        "average_pace_min_km": pace_str,
        "average_heartrate": avg_hr,
        "max_heartrate": max_hr,
        "splits": parsed_splits
    }
