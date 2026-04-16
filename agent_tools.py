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
            "description": "Use this tool to fetch the deep, kilometer-by-kilometer details (splits) of a single specific workout. You must already know the activity_id (usually obtained by calling get_recent_workouts first). Call this when the user asks specifically about a single run, or when you need to analyze pacing strategy and heart rate drift.",
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

AVAILABLE_TOOLS = [
    record_core_memory_tool, 
    record_milestone_tool,
    retrieve_core_memories_tool,
    retrieve_latest_core_memory_tool,
    retrieve_milestones_tool,
    retrieve_latest_milestone_tool,
    get_recent_workouts_tool,
    get_specific_workout_tool
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
            results.append(f"ID: {doc.id} | Date: {date} | Name: {name} | Dist: {dist}km | Pace: {pace}/km | Avg HR: {hr}")
            
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
        
        result_parts = [
            f"Activity ID: {activity_id}",
            f"Name: {name}",
            f"Date: {date}",
            f"Distance: {dist}km",
            f"Pace: {pace}/km",
            f"Avg HR: {hr} BPM",
            f"Description: {desc}",
            "--- Splits ---"
        ]
        
        splits = data.get("splits", [])
        if not splits:
            result_parts.append("No split data available.")
        else:
            for idx, split in enumerate(splits):
                s_dist = split.get("distance_km", 0)
                s_pace = split.get("average_pace_min_km", "N/A")
                s_hr = split.get("average_heartrate", "N/A")
                result_parts.append(f"Split {idx + 1}: {s_pace}/km, {s_hr} BPM.")
        
        return "\n".join(result_parts)
    except Exception as e:
        logger.error(f"Unexpected error in get_specific_workout_from_db: {e}")
        return f"System Error: Could not retrieve workout. {e}"
