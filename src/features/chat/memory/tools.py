import uuid
from datetime import datetime, timezone
from src.shared.dependencies import db
from src.shared.logger import logger
from src.features.chat.memory.utils import DistanceCategory, parse_time_to_seconds

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
            "description": "Use this tool to record specific athletic achievements, such as longest run distances, qualitative milestones, or non-timed achievements.",
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

log_personal_best_tool = {
    "function_declarations": [
        {
            "name": "log_personal_best",
            "description": "Log a new Personal Best (PB) for an officially timed standard distance. Rejects the time if it's slower than current PB.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "distance_category": {
                        "type": "STRING",
                        "description": "The standard distance category (e.g. 1k, 1mi, 3k, 5k, 10k, 15k, 10mi, Half-Marathon, Marathon, 50k)."
                    },
                    "time_string": {
                        "type": "STRING",
                        "description": "The exact time achieved (e.g. 24:30 or 1:45:15)."
                    },
                    "activity_id": {
                        "type": "STRING",
                        "description": "The ID of the activity where this PB was achieved."
                    }
                },
                "required": ["distance_category", "time_string", "activity_id"]
            }
        }
    ]
}

get_personal_best_tool = {
    "function_declarations": [
        {
            "name": "get_personal_best",
            "description": "Retrieve the current personal best or history of personal bests for a standard distance.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "distance_category": {
                        "type": "STRING",
                        "description": "The standard distance category (e.g. 5k, 10k)."
                    },
                    "include_history": {
                        "type": "BOOLEAN",
                        "description": "If true, fetches the chronological history of past PBs for this distance. Defaults to False."
                    }
                },
                "required": ["distance_category"]
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

async def log_personal_best(user_id: str, distance_category: str, time_string: str, activity_id: str):
    """
    Checks the personal_bests collection.
    Saves if faster or new. Rejects if slower.
    """
    try:
        new_seconds = parse_time_to_seconds(time_string)
    except ValueError as e:
        return {"status": "error", "message": f"Invalid time format: {e}"}

    # Fetch all PBs, then filter by distance
    all_pbs = await db.list(f"users/{user_id}/personal_bests")
    distance_pbs = [pb for pb in all_pbs if pb.get("distance_category") == distance_category]
    
    if distance_pbs:
        distance_pbs.sort(key=lambda x: x.get("time_seconds", float('inf')))
        current_pb = distance_pbs[0]
        if new_seconds >= current_pb.get("time_seconds", 0):
            old_time = current_pb.get("time_string", str(current_pb.get("time_seconds")) + "s")
            return {
                "status": "rejected",
                "message": f"Action rejected. The current PB for {distance_category} is {old_time}. Inform the athlete this was a great run but not a record."
            }

    doc_id = str(uuid.uuid4())
    data = {
        "distance_category": distance_category,
        "time_string": time_string,
        "time_seconds": new_seconds,
        "activity_id": str(activity_id),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.put(f"users/{user_id}/personal_bests", doc_id, data)
    return {"status": "success", "message": f"Successfully logged new {distance_category} PB of {time_string}!"}

async def get_personal_best(user_id: str, distance_category: str, include_history: bool = False):
    """
    Retrieves the PB or history of PBs for a given distance.
    """
    all_pbs = await db.list(f"users/{user_id}/personal_bests")
    distance_pbs = [pb for pb in all_pbs if pb.get("distance_category") == distance_category]
    
    if not distance_pbs:
        return {"status": "success", "personal_bests": []}
        
    if include_history:
        distance_pbs.sort(key=lambda x: x.get("created_at", ""))
        return {"status": "success", "personal_bests": distance_pbs}
    else:
        distance_pbs.sort(key=lambda x: x.get("time_seconds", float('inf')))
        return {"status": "success", "personal_bests": [distance_pbs[0]]}
