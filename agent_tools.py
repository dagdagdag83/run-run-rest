import uuid
from datetime import datetime, timezone
from dependencies import db

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

AVAILABLE_TOOLS = [
    record_core_memory_tool, 
    record_milestone_tool,
    retrieve_core_memories_tool,
    retrieve_latest_core_memory_tool,
    retrieve_milestones_tool,
    retrieve_latest_milestone_tool
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
