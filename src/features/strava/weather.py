import httpx
from datetime import datetime
from logger import logger

def get_condition_from_wmo(code: int) -> str:
    """Maps WMO weather codes to human readable strings."""
    if code == 0:
        return "Clear"
    elif code in [1, 2, 3]:
        # 3 is technically Overcast, but test checks for Overcast for 3
        if code == 3:
            return "Overcast"
        return "Cloudy"
    elif code in [45, 48]:
        return "Fog"
    elif code in [51, 53, 55, 56, 57]:
        return "Drizzle"
    elif code in [61, 63, 65, 66, 67, 80, 81, 82]:
        return "Rain"
    elif code in [71, 73, 75, 77, 85, 86]:
        return "Snow"
    elif code in [95, 96, 99]:
        return "Thunderstorm"
    return "Unknown"

async def enrich_with_weather(raw_strava_data: dict) -> dict | None:
    """
    Fetches historical weather data from Open-Meteo for the duration of the Strava activity.
    """
    try:
        # 1. Location Logic
        latlng = raw_strava_data.get("start_latlng")
        trainer = raw_strava_data.get("trainer", False)
        likely_indoors = bool(trainer or not latlng or len(latlng) < 2)
        
        if not latlng or len(latlng) < 2:
            lat = 63.43
            lng = 10.39
            logger.info("start_latlng missing or invalid, defaulting to Trondheim (63.43, 10.39)")
        else:
            lat = latlng[0]
            lng = latlng[1]

        # 2. Time Logic
        start_date_str = raw_strava_data.get("start_date")
        if not start_date_str:
            logger.warning("No start_date found in activity data.")
            return None
        
        # Parse start_date from e.g. "2024-05-14T14:52:00Z"
        start_dt = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        date_str = start_dt.strftime("%Y-%m-%d")
        # Find exact hour string that matches Open-Meteo format "YYYY-MM-DDTHH:00"
        target_hour_str = start_dt.strftime("%Y-%m-%dT%H:00")

        # 3. Open-Meteo API Call
        url = f"https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lng,
            "start_date": date_str,
            "end_date": date_str,
            "hourly": "temperature_2m,weather_code,wind_speed_10m"
        }

        logger.info(f"Fetching weather for lat={lat}, lng={lng} at {target_hour_str}")
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        
        # 4. Extract target hour
        try:
            time_idx = times.index(target_hour_str)
        except ValueError:
            logger.warning(f"Target hour {target_hour_str} not found in Open-Meteo response.")
            return None

        temp_c = hourly.get("temperature_2m", [])[time_idx]
        wmo_code = hourly.get("weather_code", [])[time_idx]
        wind_speed_kmh = hourly.get("wind_speed_10m", [])[time_idx]
        
        condition = get_condition_from_wmo(wmo_code) if wmo_code is not None else "Unknown"
        logger.info(f"Weather fetched: {temp_c}C, {condition}, {wind_speed_kmh}km/h wind")

        # 5. Build response dict
        return {
            "temp_c": float(temp_c) if temp_c is not None else 0.0,
            "condition": condition,
            "wind_kph": float(wind_speed_kmh) if wind_speed_kmh is not None else 0.0,
            "likely_indoors": likely_indoors
        }

    except Exception as e:
        logger.error(f"Weather enrichment failed: {e}")
        return None
