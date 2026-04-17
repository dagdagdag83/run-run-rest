import google.api_core.exceptions
from google.cloud import firestore
from datetime import datetime, timezone, timedelta
from src.shared.dependencies import db
from src.shared.logger import logger

get_recent_workouts_tool = {
    "function_declarations": [
        {
            "name": "get_recent_workouts",
            "description": "Use this tool to fetch the user's actual running data and Strava history. You can filter by distance to find specific types of runs (e.g., set min_distance_km to 15 to find long runs). Call this whenever you need to analyze recent performance, check training volume, or answer questions about specific recent runs. Do NOT hallucinate workout data; always use this tool.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "days_back": {
                        "type": "INTEGER",
                        "description": "Number of days back to look for workouts. Defaults to 7."
                    },
                    "limit": {
                        "type": "INTEGER",
                        "description": "Maximum number of workouts to return. Defaults to 10."
                    },
                    "min_distance_km": {
                        "type": "NUMBER",
                        "description": "Minimum distance in kilometers to filter by."
                    },
                    "max_distance_km": {
                        "type": "NUMBER",
                        "description": "Maximum distance in kilometers to filter by."
                    }
                }
            }
        }
    ]
}

get_specific_workout_tool = {
    "function_declarations": [
        {
            "name": "get_specific_workout",
            "description": "Use this tool to fetch the deep, kilometer-by-kilometer details (splits) of a single specific workout. This includes weather data and physiological metrics like training zones and intensity scores. You must already know the activity_id (usually obtained by calling get_recent_workouts first). Call this when the user asks specifically about a single run, or when you need to analyze pacing strategy and heart rate drift.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "activity_id": {
                        "type": "INTEGER",
                        "description": "The Strava activity_id of the workout."
                    }
                },
                "required": ["activity_id"]
            }
        }
    ]
}

update_workout_notes_tool = {
    "function_declarations": [
        {
            "name": "update_workout_notes",
            "description": "Use this tool to record the user's subjective thoughts, feelings of fatigue, weather conditions, or pain related to a SPECIFIC run. CRITICAL: This tool OVERWRITES the existing notes. If the workout already has notes (which you can see from your read tools), you must act as an editor: compose a new, consolidated note that preserves the important historical context while integrating the new feedback, and pass that fully synthesized string into the 'notes' argument.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "activity_id": {
                        "type": "INTEGER",
                        "description": "The Strava activity_id of the workout."
                    },
                    "notes": {
                        "type": "STRING",
                        "description": "The full consolidated, subjective note for the workout."
                    }
                },
                "required": ["activity_id", "notes"]
            }
        }
    ]
}

async def get_user_workouts_from_db(user_id: str, days_back: int = 7, limit: int = 10, min_distance_km: float = None, max_distance_km: float = None):
    """Queries the user's workouts subcollection."""
    try:
        if not hasattr(db, "_db"):
            return "Error: Tool requires Firestore DB backend."
            
        collection_ref = db._db.collection(f"users/{user_id}/workouts")
        query = collection_ref

        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        # Native where clauses
        query = query.where(filter=firestore.FieldFilter("start_date_local", ">=", cutoff_date))
        
        if min_distance_km is not None:
            query = query.where(filter=firestore.FieldFilter("distance_km", ">=", min_distance_km))
            
        if max_distance_km is not None:
            query = query.where(filter=firestore.FieldFilter("distance_km", "<=", max_distance_km))
            
        from google.cloud import firestore as firestore_module
        query = query.order_by("start_date_local", direction=firestore_module.Query.DESCENDING)
        if limit is not None:
            query = query.limit(limit)

        docs = await query.get()
        if not docs:
            return "No recent workouts found."

        results = []
        for doc in docs:
            data = doc.to_dict()
            date = data.get("start_date_local", "Unknown Date")
            name = data.get("name", "Unnamed Run")
            dist = data.get("distance_km", 0)
            pace = data.get("average_pace_min_km", "N/A")
            hr = data.get("average_heartrate", "N/A")
            notes = data.get("user_notes", "")
            notes_str = f" | Notes: {notes}" if notes else ""
            results.append(f"ID: {doc.id} | Date: {date} | Name: {name} | Dist: {dist}km | Pace: {pace}/km | Avg HR: {hr}{notes_str}")
            
        return "\n".join(results)
        
    except google.api_core.exceptions.FailedPrecondition as e:
        logger.error(f"Firestore Composite Index Error in get_user_workouts_from_db: {e}")
        return "System Error: Missing Firestore index. The engineer has been notified."
    except Exception as e:
        logger.error(f"Unexpected error in get_user_workouts_from_db: {e}")
        return f"System Error: Could not retrieve workouts. {e}"

async def get_specific_workout_from_db(user_id: str, activity_id: int):
    """Fetches a single specific workout from the db including detailed split data."""
    try:
        if not hasattr(db, "_db"):
            return "Error: Tool requires Firestore DB backend."
            
        doc_ref = db._db.collection(f"users/{user_id}/workouts").document(str(activity_id))
        doc = await doc_ref.get()
        
        if not doc.exists:
            return f"Workout with activity_id {activity_id} could not be found."
            
        data = doc.to_dict()
        
        date = data.get("start_date_local", "Unknown Date")
        name = data.get("name", "Unnamed Run")
        dist = data.get("distance_km", 0)
        pace = data.get("average_pace_min_km", "N/A")
        hr = data.get("average_heartrate", "N/A")
        desc = data.get("description") or "No description"
        notes = data.get("user_notes", "No notes recorded.")
        sport_type = data.get("sport_type", "Unknown")
        device_name = data.get("device_name", "Unknown")
        
        weather = data.get("weather")
        if weather:
            indoors_str = str(weather.get("likely_indoors", False))
            weather_str = f"{weather.get('temp_c')}C, {weather.get('condition')}, {weather.get('wind_kph')}km/h wind"
        else:
            indoors_str = "Unknown"
            weather_str = "No weather data"
        
        metrics = data.get("metrics")
        if metrics:
            metrics_str = f"Zone: {metrics.get('primary_zone')} | Intensity: {metrics.get('intensity_score')} (Method: {metrics.get('calculation_method')})"
        else:
            metrics_str = "No physiological metrics available"

        result_parts = [
            f"Activity ID: {activity_id}",
            f"Name: {name}",
            f"Date: {date}",
            f"Sport Category: {sport_type}",
            f"Device: {device_name}",
            f"Likely Indoors: {indoors_str}",
            f"Distance: {dist}km",
            f"Pace: {pace}/km",
            f"Avg HR: {hr} BPM",
            f"Weather: {weather_str}",
            f"Physiology: {metrics_str}",
            f"Description: {desc}",
            f"User Subjective Notes: {notes}",
            "--- Splits ---"
        ]
        
        splits = data.get("splits", [])
        if not splits:
            result_parts.append("No split data available")
        else:
            for idx, split in enumerate(splits):
                s_dist = split.get("distance_km", 0)
                s_pace = split.get("average_pace_min_km", "N/A")
                s_hr = split.get("average_heartrate", "N/A")
                result_parts.append(f"Split {idx + 1}: {s_pace}/km, {s_hr} BPM")
        
        return " | ".join(result_parts)
    except Exception as e:
        logger.error(f"Unexpected error in get_specific_workout_from_db: {e}")
        return f"System Error: Could not retrieve workout. {e}"

async def update_workout_notes_in_db(user_id: str, activity_id: int, notes: str):
    """Updates the user_notes field for a specific workout document."""
    try:
        await db.put(f"users/{user_id}/workouts", str(activity_id), {"user_notes": notes}, merge=True)
    except Exception as e:
        logger.error(f"Unexpected error updating notes for workout {activity_id}: {e}")
