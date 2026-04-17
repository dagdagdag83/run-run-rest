from datetime import datetime, timezone
from google.cloud import firestore
from src.shared.dependencies import db
from src.shared.logger import logger

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
