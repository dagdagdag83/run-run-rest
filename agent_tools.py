import uuid
from datetime import datetime, timezone, timedelta
import google.api_core.exceptions
from google.cloud import firestore
from dependencies import db
from logger import logger

record_core_memory_tool = {
    "function_declarations": [
        {
            "name": "record_core_memory",
            "description": "Use this tool to silently record important facts, injuries, goals, or life events the user mentions so you do not forget them later.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "memory_text": {
                        "type": "STRING",
                        "description": "The string to remember about the user"
                    }
                },
                "required": ["memory_text"]
            }
        }
    ]
}

record_milestone_tool = {
    "function_declarations": [
        {
            "name": "record_milestone",
            "description": "Use this tool to record specific athletic achievements, such as Personal Bests (PBs), longest run distances, fastest splits, or best interval times.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "milestone_text": {
                        "type": "STRING",
                        "description": "A description of the user's athletic achievement or milestone"
                    }
                },
                "required": ["milestone_text"]
            }
        }
    ]
}

set_training_directive_tool = {
    "function_declarations": [
        {
            "name": "set_training_directive",
            "description": "Use this tool to record a new training philosophy, habit, or rule the user wants to follow for an upcoming training block. Do NOT use this for past achievements. Call this silently when the user proposes a strategic shift in their training (e.g., 'I want to run outside more this month'). Calculate an appropriate target_date based on their timeframe.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "focus": {
                        "type": "STRING",
                        "description": "The description of the training focus or newly defined rule."
                    },
                    "rationale": {
                        "type": "STRING",
                        "description": "The logic or reason behind this directive."
                    },
                    "target_date": {
                        "type": "STRING",
                        "description": "The calculated target date based on the timeframe, formatted YYYY-MM-DD."
                    }
                },
                "required": ["focus", "rationale", "target_date"]
            }
        }
    ]
}

remove_training_directive_tool = {
    "function_declarations": [
        {
            "name": "remove_training_directive",
            "description": "Use this tool to delete an active training directive. Call this if the user explicitly abandons a goal, or if you notice the target_date has passed, you have asked the user about it, and they agree it is time to clear it.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "focus": {
                        "type": "STRING",
                        "description": "The exact focus text of the directive to remove."
                    }
                },
                "required": ["focus"]
            }
        }
    ]
}

retrieve_core_memories_tool = {
    "function_declarations": [
        {
            "name": "retrieve_core_memories",
            "description": "Retrieve previously recorded core memories of the user. You can limit the number of entries returned.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "max_results": {
                        "type": "INTEGER",
                        "description": "Maximum number of memories to retrieve. If not provided, retrieves all."
                    }
                }
            }
        }
    ]
}

retrieve_latest_core_memory_tool = {
    "function_declarations": [
        {
            "name": "retrieve_latest_core_memory",
            "description": "Retrieve the most recently recorded core memory of the user. Use this when you only need the single most recent entry.",
        }
    ]
}

retrieve_milestones_tool = {
    "function_declarations": [
        {
            "name": "retrieve_milestones",
            "description": "Retrieve previously recorded athletic milestones of the user. You can limit the number of entries returned.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "max_results": {
                        "type": "INTEGER",
                        "description": "Maximum number of milestones to retrieve. If not provided, retrieves all."
                    }
                }
            }
        }
    ]
}

retrieve_latest_milestone_tool = {
    "function_declarations": [
        {
            "name": "retrieve_latest_milestone",
            "description": "Retrieve the most recently recorded athletic milestone of the user. Use this when you only need the single most recent entry.",
        }
    ]
}

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

get_training_directives_tool = {
    "function_declarations": [
        {
            "name": "get_training_directives",
            "description": "Use this tool to fetch the user's training directives. You can request either 'all' or 'active' (which filters out directives where the target_date is in the past).",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "status": {
                        "type": "STRING",
                        "description": "The status of directives to fetch. Must be either 'all' or 'active'."
                    }
                },
                "required": ["status"]
            }
        }
    ]
}

update_biometrics_tool = {
    "function_declarations": [
        {
            "name": "update_biometrics",
            "description": "Use this tool to update the user's biological metrics. You can update one, multiple, or all fields at once. IMPORTANT: If the user gives you their age, calculate their birth_year based on the current year before passing it to this tool. Call this silently when the user shares physical stats about themselves.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "height_cm": {"type": "NUMBER", "description": "Height in centimeters"},
                    "weight_kg": {"type": "NUMBER", "description": "Weight in kilograms"},
                    "birth_year": {"type": "INTEGER", "description": "The birth year of the user"},
                    "max_hr": {"type": "INTEGER", "description": "Maximum heart rate"},
                    "resting_hr": {"type": "INTEGER", "description": "Resting heart rate"},
                    "threshold_hr": {"type": "INTEGER", "description": "Lactate threshold heart rate"},
                    "sex": {"type": "STRING", "description": "Biological sex, 'M' or 'F'"}
                }
            }
        }
    ]
}

get_biometrics_tool = {
    "function_declarations": [
        {
            "name": "get_biometrics",
            "description": "Use this tool to retrieve the user's current physical stats and biological metrics.",
        }
    ]
}

AVAILABLE_TOOLS = [
    record_core_memory_tool, 
    record_milestone_tool,
    retrieve_core_memories_tool,
    retrieve_latest_core_memory_tool,
    retrieve_milestones_tool,
    retrieve_latest_milestone_tool,
    get_recent_workouts_tool,
    get_specific_workout_tool,
    update_workout_notes_tool,
    set_training_directive_tool,
    remove_training_directive_tool,
    get_training_directives_tool,
    update_biometrics_tool,
    get_biometrics_tool
]

async def save_core_memory(user_id: str, text: str):
    """Saves a memory to the users/{user_id}/core_memories subcollection."""
    doc_id = str(uuid.uuid4())
    data = {"text": text, "created_at": datetime.now(timezone.utc).isoformat()}
    await db.put(f"users/{user_id}/core_memories", doc_id, data)

async def save_milestone(user_id: str, text: str):
    """Saves an athletic milestone to the users/{user_id}/milestones subcollection."""
    doc_id = str(uuid.uuid4())
    data = {"text": text, "created_at": datetime.now(timezone.utc).isoformat()}
    await db.put(f"users/{user_id}/milestones", doc_id, data)

async def get_core_memories(user_id: str, max_results: int = None):
    """Retrieves all or a limited number of core memories for the user."""
    return await db.list(f"users/{user_id}/core_memories", limit=max_results, order_by="created_at", descending=True)

async def get_latest_core_memory(user_id: str):
    """Retrieves the most recent core memory for the user."""
    results = await db.list(f"users/{user_id}/core_memories", limit=1, order_by="created_at", descending=True)
    return results[0] if results else None

async def get_milestones(user_id: str, max_results: int = None):
    """Retrieves all or a limited number of milestones for the user."""
    return await db.list(f"users/{user_id}/milestones", limit=max_results, order_by="created_at", descending=True)

async def get_latest_milestone(user_id: str):
    """Retrieves the most recent milestone for the user."""
    results = await db.list(f"users/{user_id}/milestones", limit=1, order_by="created_at", descending=True)
    return results[0] if results else None

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

async def set_training_directive_in_db(user_id: str, focus: str, rationale: str, target_date: str):
    """Appends a new training directive to the user's active_directives array using Firestore ArrayUnion."""
    try:
        data = {
            "focus": focus,
            "rationale": rationale,
            "target_date": target_date
        }
        await db.put("users", user_id, {"active_directives": firestore.ArrayUnion([data])}, merge=True)
    except Exception as e:
        logger.error(f"Unexpected error appending training directive for user {user_id}: {e}")

async def remove_training_directive_from_db(user_id: str, focus: str):
    """Removes a training directive from the user's active_directives array by matching the focus string."""
    try:
        doc = await db.get("users", user_id)
        if not doc:
            return
            
        current_directives = doc.get("active_directives", [])
        new_directives = [d for d in current_directives if d.get("focus") != focus]
        
        await db.put("users", user_id, {"active_directives": new_directives}, merge=True)
    except Exception as e:
        logger.error(f"Unexpected error removing training directive for user {user_id}: {e}")

async def get_training_directives_from_db(user_id: str, status: str = "active"):
    """Fetches training directives for the user. If status is 'active', filters out past target_dates."""
    try:
        doc = await db.get("users", user_id)
        if not doc:
            return "No training directives found."
            
        directives = doc.get("active_directives", [])
        if not directives:
            return "No training directives found."
            
        if status == "active":
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            active_list = []
            for d in directives:
                target = d.get("target_date", "")
                if target >= today_str or not target:
                    active_list.append(d)
            directives = active_list
            
        if not directives:
            return f"No {status} training directives found."
            
        results = [f"--- {status.upper()} DIRECTIVES ---"]
        for d in directives:
            results.append(f"- Focus: {d.get('focus')}\n  Rationale: {d.get('rationale')}\n  Target Date: {d.get('target_date')}")
            
        return "\n".join(results)
    except Exception as e:
        logger.error(f"Unexpected error getting training directives for user {user_id}: {e}")
        return f"System Error: Could not retrieve training directives. {e}"

async def update_user_biometrics_in_db(user_id: str, height_cm: float = None, weight_kg: float = None, birth_year: int = None, max_hr: int = None, resting_hr: int = None, threshold_hr: int = None, sex: str = None):
    """Updates the user's biometrics document with only the provided fields."""
    try:
        fields = {
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "birth_year": birth_year,
            "max_hr": max_hr,
            "resting_hr": resting_hr,
            "threshold_hr": threshold_hr,
            "sex": sex
        }
        filtered = {k: v for k, v in fields.items() if v is not None}
        if filtered:
            await db.put("users", user_id, {"biometrics": filtered}, merge=True)
    except Exception as e:
        logger.error(f"Unexpected error updating biometrics for user {user_id}: {e}")

async def get_user_biometrics_from_db(user_id: str):
    """Fetches the user's biometrics and formats them nicely."""
    try:
        doc = await db.get("users", user_id)
        if not doc:
            return "No biometrics found."
        
        biometrics = doc.get("biometrics", {})
        if not biometrics:
            return "No biometrics found."
            
        parts = []
        for k, v in biometrics.items():
            parts.append(f"{k.replace('_', ' ').title()}: {v}")
        return " | ".join(parts)
    except Exception as e:
        logger.error(f"Unexpected error getting biometrics for user {user_id}: {e}")
        return f"System Error: Could not retrieve biometrics. {e}"
