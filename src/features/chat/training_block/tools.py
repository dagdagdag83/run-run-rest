import uuid
from datetime import datetime, timezone
from src.shared.dependencies import db
from src.shared.logger import logger

set_training_block_tool = {
    "function_declarations": [
        {
            "name": "set_training_block",
            "description": "Use this tool to proactively set the user's current training phase. Call this when you agree on a new primary goal. A 'Training Block' defines a specific phase of training, goals, and maintenance habits. If an existing block is active, it will automatically be archived.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "phase_name": {
                        "type": "STRING",
                        "description": "Short name for the block, e.g. 'Base Building', 'Marathon Prep'"
                    },
                    "primary_target": {
                        "type": "STRING",
                        "description": "The main goal of this block."
                    },
                    "secondary_targets": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": "A list of secondary goals."
                    },
                    "maintenance_habits": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": "A list of habits or rules to maintain during this block."
                    },
                    "target_date": {
                        "type": "STRING",
                        "description": "The date when this block concludes, formatted YYYY-MM-DD."
                    }
                },
                "required": ["phase_name", "primary_target", "secondary_targets", "maintenance_habits", "target_date"]
            }
        }
    ]
}

update_training_habits_tool = {
    "function_declarations": [
        {
            "name": "update_training_habits",
            "description": "Use this tool to proactively modify the maintenance habits on the currently active training block. You can pass one or more habits to add, and one or more to remove.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "habits_to_add": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": "List of the exact habit strings to add."
                    },
                    "habits_to_remove": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": "List of the exact habit strings to remove."
                    }
                }
            }
        }
    ]
}

mark_block_achieved_tool = {
    "function_declarations": [
        {
            "name": "mark_block_achieved",
            "description": "Use this tool to mark the current active training block as achieved (archives it) when the athlete hits the target. Provide a robust summary note describing their achievement and final thoughts.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "summary_notes": {
                        "type": "STRING",
                        "description": "Your detailed notes and summary of their training block."
                    }
                },
                "required": ["summary_notes"]
            }
        }
    ]
}

get_training_blocks_tool = {
    "function_declarations": [
        {
            "name": "get_training_blocks",
            "description": "Use this tool to look up past archived goals and phases to track long-term progress, or fetch the active block if needed.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "status": {
                        "type": "STRING",
                        "description": "Filter by status, typically 'active' or 'archived'."
                    }
                }
            }
        }
    ]
}

async def set_training_block_in_db(user_id: str, phase_name: str, primary_target: str, secondary_targets: list, maintenance_habits: list, target_date: str):
    """Sets a new training block and archives any existing active blocks."""
    try:
        from google.cloud import firestore as firestore_module
        
        # 1. Archive existing active blocks
        collection_ref = db._db.collection(f"users/{user_id}/training_blocks")
        active_docs = await collection_ref.where(filter=firestore_module.FieldFilter("status", "==", "active")).get()
        
        for doc in active_docs:
            await db.put(f"users/{user_id}/training_blocks", doc.id, {"status": "archived"}, merge=True)
            
        # 2. Create the new block
        doc_id = str(uuid.uuid4())
        data = {
            "phase_name": phase_name,
            "primary_target": primary_target,
            "secondary_targets": secondary_targets,
            "maintenance_habits": maintenance_habits,
            "target_date": target_date,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.put(f"users/{user_id}/training_blocks", doc_id, data)
    except Exception as e:
        logger.error(f"Unexpected error setting training block for user {user_id}: {e}")

async def update_training_habits_in_db(user_id: str, habits_to_add: list = None, habits_to_remove: list = None):
    """Updates the habits array on the active training block."""
    try:
        from google.cloud import firestore as firestore_module
        collection_ref = db._db.collection(f"users/{user_id}/training_blocks")
        active_docs = await collection_ref.where(filter=firestore_module.FieldFilter("status", "==", "active")).limit(1).get()
        
        if not active_docs:
            return "Error: No active training block found."
            
        doc = active_docs[0]
        data = doc.to_dict()
        habits = data.get("maintenance_habits", [])
        
        if habits_to_remove:
            habits = [h for h in habits if h not in habits_to_remove]
        if habits_to_add:
            # avoid duplicates blindly
            for h in habits_to_add:
                if h not in habits:
                    habits.append(h)
                    
        await db.put(f"users/{user_id}/training_blocks", doc.id, {"maintenance_habits": habits}, merge=True)
    except Exception as e:
        logger.error(f"Unexpected error updating training habits for user {user_id}: {e}")

async def mark_block_achieved_in_db(user_id: str, summary_notes: str):
    """Archives the active block and saves the agent's summary notes."""
    try:
        from google.cloud import firestore as firestore_module
        collection_ref = db._db.collection(f"users/{user_id}/training_blocks")
        active_docs = await collection_ref.where(filter=firestore_module.FieldFilter("status", "==", "active")).limit(1).get()
        
        if not active_docs:
            return "Error: No active training block found."
            
        doc = active_docs[0]
        data = {
            "status": "archived",
            "agent_summary_notes": summary_notes,
            "achieved_at": datetime.now(timezone.utc).isoformat()
        }
        await db.put(f"users/{user_id}/training_blocks", doc.id, data, merge=True)
    except Exception as e:
        logger.error(f"Unexpected error marking block achieved for user {user_id}: {e}")

async def get_training_blocks_from_db(user_id: str, status: str = None):
    """Fetches training blocks, optimally filtering by status."""
    try:
        from google.cloud import firestore as firestore_module
        collection_ref = db._db.collection(f"users/{user_id}/training_blocks")
        query = collection_ref
        
        if status:
            query = query.where(filter=firestore_module.FieldFilter("status", "==", status))
            
        query = query.order_by("created_at", direction=firestore_module.Query.DESCENDING)
        docs = await query.get()
        
        if not docs:
            return f"No training blocks found{f' with status {status}' if status else ''}."
            
        results = [f"--- TRAINING BLOCKS ---"]
        for doc in docs:
            d = doc.to_dict()
            parts = [f"Phase: {d.get('phase_name', 'Unnamed')}"]
            parts.append(f"Status: {d.get('status', 'unknown')}")
            parts.append(f"Target Date: {d.get('target_date', 'N/A')}")
            parts.append(f"Primary Target: {d.get('primary_target')}")
            
            sec = d.get('secondary_targets', [])
            if sec:
                parts.append(f"Secondary Targets: {', '.join(sec)}")
                
            habits = d.get('maintenance_habits', [])
            if habits:
                parts.append(f"Maintenance Habits: {', '.join(habits)}")
                
            summary = d.get('agent_summary_notes')
            if summary:
                parts.append(f"Agent Summary: {summary}")
                
            results.append(" | ".join(parts))
            
        return "\n".join(results)
    except Exception as e:
        logger.error(f"Unexpected error getting training blocks for user {user_id}: {e}")
        return f"System Error: Could not retrieve training blocks. {e}"
