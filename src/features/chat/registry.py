from google.genai import types
from src.shared.logger import logger

from src.features.chat.training_block.tools import (
    set_training_block_tool, update_training_habits_tool, mark_block_achieved_tool, get_training_blocks_tool,
    set_training_block_in_db, update_training_habits_in_db, mark_block_achieved_in_db, get_training_blocks_from_db
)
from src.features.chat.workout.tools import (
    get_recent_workouts_tool, get_specific_workout_tool, update_workout_notes_tool,
    get_user_workouts_from_db, get_specific_workout_from_db, update_workout_notes_in_db
)
from src.features.chat.memory.tools import (
    record_core_memory_tool, record_milestone_tool, log_personal_best_tool, get_personal_best_tool, retrieve_core_memories_tool, retrieve_latest_core_memory_tool, retrieve_milestones_tool, retrieve_latest_milestone_tool,
    save_core_memory, save_milestone, log_personal_best, get_personal_best, get_core_memories, get_latest_core_memory, get_milestones, get_latest_milestone
)
from src.features.chat.librarian.tools import (
    recall_past_conversation_tool, recall_past_conversation
)
from src.features.chat.baseline.tools import (
    set_training_directive_tool, remove_training_directive_tool, get_training_directives_tool, update_biometrics_tool, get_biometrics_tool,
    set_training_directive_in_db, remove_training_directive_from_db, get_training_directives_from_db, update_user_biometrics_in_db, get_user_biometrics_from_db
)

AVAILABLE_TOOLS = [
    record_core_memory_tool, 
    record_milestone_tool,
    log_personal_best_tool,
    get_personal_best_tool,
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
    get_biometrics_tool,
    set_training_block_tool,
    update_training_habits_tool,
    mark_block_achieved_tool,
    get_training_blocks_tool,
    recall_past_conversation_tool
]

async def execute_tool(call, sub: str) -> types.Part:
    """
    Executes the appropriate tool function based on the call name.
    """
    name = call.name
    args = call.args

    if name == "record_core_memory":
        memory_text = args.get("memory_text")
        if memory_text:
            await save_core_memory(sub, memory_text)
            logger.info("Tool executed: record_core_memory", extra={"user_id": sub, "memory_text": memory_text})
        return types.Part.from_function_response(name=name, response={"status": "success"})

    elif name == "record_milestone":
        milestone_text = args.get("milestone_text")
        if milestone_text:
            await save_milestone(sub, milestone_text)
            logger.info("Tool executed: record_milestone", extra={"user_id": sub, "milestone_text": milestone_text})
        return types.Part.from_function_response(name=name, response={"status": "success"})

    elif name == "retrieve_core_memories":
        max_results = args.get("max_results")
        try: max_results = int(max_results) if max_results is not None else None
        except ValueError: max_results = None
        memories = await get_core_memories(sub, max_results)
        logger.info("Tool executed: retrieve_core_memories", extra={"user_id": sub, "max_results": max_results})
        return types.Part.from_function_response(name=name, response={"memories": memories})

    elif name == "retrieve_latest_core_memory":
        memory = await get_latest_core_memory(sub)
        logger.info("Tool executed: retrieve_latest_core_memory", extra={"user_id": sub})
        return types.Part.from_function_response(name=name, response={"memory": memory})

    elif name == "retrieve_milestones":
        max_results = args.get("max_results")
        try: max_results = int(max_results) if max_results is not None else None
        except ValueError: max_results = None
        milestones = await get_milestones(sub, max_results)
        logger.info("Tool executed: retrieve_milestones", extra={"user_id": sub, "max_results": max_results})
        return types.Part.from_function_response(name=name, response={"milestones": milestones})

    elif name == "retrieve_latest_milestone":
        milestone = await get_latest_milestone(sub)
        logger.info("Tool executed: retrieve_latest_milestone", extra={"user_id": sub})
        return types.Part.from_function_response(name=name, response={"milestone": milestone})

    elif name == "log_personal_best":
        dist = args.get("distance_category")
        time_str = args.get("time_string")
        act_id = args.get("activity_id")
        if dist and time_str and act_id:
            res = await log_personal_best(sub, dist, time_str, act_id)
            logger.info("Tool executed: log_personal_best", extra={"user_id": sub, "distance": dist, "time": time_str})
            return types.Part.from_function_response(name=name, response=res)
        return types.Part.from_function_response(name=name, response={"status": "error", "message": "missing arguments"})

    elif name == "get_personal_best":
        dist = args.get("distance_category")
        incl_hist = args.get("include_history", False)
        if dist:
            res = await get_personal_best(sub, dist, incl_hist)
            logger.info("Tool executed: get_personal_best", extra={"user_id": sub, "distance": dist})
            return types.Part.from_function_response(name=name, response=res)
        return types.Part.from_function_response(name=name, response={"status": "error", "message": "distance_category required"})

    elif name == "get_recent_workouts":
        days_back = args.get("days_back", 7)
        limit = args.get("limit", 10)
        min_dist = args.get("min_distance_km")
        max_dist = args.get("max_distance_km")
        try: days_back = int(days_back) if days_back is not None else 7
        except (ValueError, TypeError): days_back = 7
        try: limit = int(limit) if limit is not None else 10
        except (ValueError, TypeError): limit = 10
        try: min_dist = float(min_dist) if min_dist is not None else None
        except (ValueError, TypeError): min_dist = None
        try: max_dist = float(max_dist) if max_dist is not None else None
        except (ValueError, TypeError): max_dist = None
        workouts_str = await get_user_workouts_from_db(sub, days_back, limit, min_dist, max_dist)
        logger.info("Tool executed: get_recent_workouts", extra={"user_id": sub, "days_back": days_back, "limit": limit, "min_distance_km": min_dist, "max_distance_km": max_dist})
        return types.Part.from_function_response(name=name, response={"workouts_summary": workouts_str})

    elif name == "get_specific_workout":
        activity_id = args.get("activity_id")
        try: activity_id = int(activity_id) if activity_id is not None else 0
        except (ValueError, TypeError): activity_id = 0
        workout_str = await get_specific_workout_from_db(sub, activity_id)
        logger.info("Tool executed: get_specific_workout", extra={"user_id": sub, "activity_id": activity_id, "workout_details": workout_str})
        return types.Part.from_function_response(name=name, response={"workout_details": workout_str})

    elif name == "update_workout_notes":
        activity_id = args.get("activity_id")
        notes = args.get("notes")
        try: activity_id = int(activity_id) if activity_id is not None else 0
        except (ValueError, TypeError): activity_id = 0
        if activity_id and notes:
            await update_workout_notes_in_db(sub, activity_id, notes)
            logger.info("Tool executed: update_workout_notes", extra={"user_id": sub, "activity_id": activity_id, "notes": notes})
        return types.Part.from_function_response(name=name, response={"status": "success"})

    elif name == "set_training_directive":
        focus = args.get("focus")
        rationale = args.get("rationale")
        target_date = args.get("target_date")
        if focus and rationale and target_date:
            await set_training_directive_in_db(sub, focus, rationale, target_date)
            logger.info("Tool executed: set_training_directive", extra={"user_id": sub, "focus": focus, "rationale": rationale, "target_date": target_date})
        return types.Part.from_function_response(name=name, response={"status": "success"})

    elif name == "remove_training_directive":
        focus = args.get("focus")
        if focus:
            await remove_training_directive_from_db(sub, focus)
            logger.info("Tool executed: remove_training_directive", extra={"user_id": sub, "focus": focus})
        return types.Part.from_function_response(name=name, response={"status": "success"})

    elif name == "get_training_directives":
        status = args.get("status", "active")
        directives_str = await get_training_directives_from_db(sub, status)
        logger.info("Tool executed: get_training_directives", extra={"user_id": sub, "status": status})
        return types.Part.from_function_response(name=name, response={"directives": directives_str})

    elif name == "update_biometrics":
        height = args.get("height_cm")
        weight = args.get("weight_kg")
        birth_yr = args.get("birth_year")
        max_hr = args.get("max_hr")
        resting_hr = args.get("resting_hr")
        thresh_hr = args.get("threshold_hr")
        sex = args.get("sex")
        await update_user_biometrics_in_db(sub, height, weight, birth_yr, max_hr, resting_hr, thresh_hr, sex)
        logger.info("Tool executed: update_biometrics", extra={"user_id": sub, "height_cm": height, "weight_kg": weight, "birth_year": birth_yr, "max_hr": max_hr, "resting_hr": resting_hr, "threshold_hr": thresh_hr, "sex": sex})
        return types.Part.from_function_response(name=name, response={"status": "success"})

    elif name == "get_biometrics":
        bio_str = await get_user_biometrics_from_db(sub)
        logger.info("Tool executed: get_biometrics", extra={"user_id": sub})
        return types.Part.from_function_response(name=name, response={"biometrics": bio_str})

    elif name == "set_training_block":
        await set_training_block_in_db(
            user_id=sub,
            phase_name=args.get("phase_name"),
            primary_target=args.get("primary_target"),
            secondary_targets=args.get("secondary_targets", []),
            maintenance_habits=args.get("maintenance_habits", []),
            target_date=args.get("target_date")
        )
        logger.info("Tool executed: set_training_block", extra={"user_id": sub})
        return types.Part.from_function_response(name=name, response={"status": "success"})

    elif name == "update_training_habits":
        await update_training_habits_in_db(sub, args.get("habits_to_add", []), args.get("habits_to_remove", []))
        logger.info("Tool executed: update_training_habits", extra={"user_id": sub})
        return types.Part.from_function_response(name=name, response={"status": "success"})

    elif name == "mark_block_achieved":
        summary = args.get("summary_notes", "No summary provided.")
        await mark_block_achieved_in_db(sub, summary)
        logger.info("Tool executed: mark_block_achieved", extra={"user_id": sub})
        return types.Part.from_function_response(name=name, response={"status": "success"})

    elif name == "get_training_blocks":
        status_filter = args.get("status")
        blocks_str = await get_training_blocks_from_db(sub, status_filter)
        logger.info("Tool executed: get_training_blocks", extra={"user_id": sub})
        return types.Part.from_function_response(name=name, response={"blocks": blocks_str})

    elif name == "recall_past_conversation":
        topic = args.get("topic")
        approximate_days_ago = args.get("approximate_days_ago")
        try: approximate_days_ago = int(approximate_days_ago) if approximate_days_ago is not None else 30
        except (ValueError, TypeError): approximate_days_ago = 30
        if topic:
            summary = await recall_past_conversation(sub, topic, approximate_days_ago)
            logger.info("Tool executed: recall_past_conversation", extra={"user_id": sub, "topic": topic})
            return types.Part.from_function_response(name=name, response={"summary": summary})
        return types.Part.from_function_response(name=name, response={"error": "topic required"})

    return types.Part.from_function_response(name=name, response={"error": "Tool not implemented"})
