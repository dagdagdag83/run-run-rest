from fastapi import APIRouter, Request, Depends
from google.genai import types
from src.features.chat.models import ChatPayload
from src.features.chat.personas import get_persona, build_system_prompt
from src.shared.dependencies import db, ai_client, get_current_user
from src.shared.logger import logger
from src.features.chat.tools import (
    AVAILABLE_TOOLS, 
    save_core_memory, save_milestone,
    get_core_memories, get_latest_core_memory,
    get_milestones, get_latest_milestone,
    get_user_workouts_from_db, get_specific_workout_from_db,
    update_workout_notes_in_db,
    set_training_directive_in_db, remove_training_directive_from_db,
    get_training_directives_from_db,
    update_user_biometrics_in_db, get_user_biometrics_from_db
)
from datetime import datetime, timezone
import time

router = APIRouter()

@router.post("/chat")
async def chat_interaction(payload: ChatPayload, request: Request, user: dict = Depends(get_current_user)):
    sub = user.get("sub")
    first_name = user.get("given_name") or user.get("name", "User")
    selected_persona_id = user.get("selected_persona", "supportive-realist")
    active_directives = user.get("active_directives", [])
    
    active_directives_str = "No active directives."
    if active_directives:
        directives_list = []
        for d in active_directives:
            directives_list.append(f"- Focus: {d.get('focus')}\n  Rationale: {d.get('rationale')}\n  Target Date: {d.get('target_date')}")
        active_directives_str = "\n".join(directives_list)
    
    persona = get_persona(selected_persona_id)
    
    session_data = await db.get(f"users/{sub}/chat_sessions", "current_session")
    if not session_data:
        session_data = {"messages": []}
        
    messages = session_data.get("messages", [])
    
    current_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    payload.message = f"[{current_timestamp}] {payload.message}"
    
    # Store the user message
    messages.append({"role": "user", "content": payload.message})
    
    if ai_client:
        try:
            genai_contents = []
            for msg in messages:
                role = "model" if msg["role"] == "assistant" else msg["role"]
                genai_contents.append(
                    types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])])
                )
                
            biometrics = user.get("biometrics")
            if biometrics:
                biometrics_parts = []
                for k, v in biometrics.items():
                    biometrics_parts.append(f"{k.replace('_', ' ').title()}: {v}")
                biometrics_str = " | ".join(biometrics_parts)
            else:
                biometrics_str = "No specific biometrics recorded."

            sys_instruct = build_system_prompt(persona, first_name, current_timestamp, active_directives_str, biometrics_str)
            
            # Build config using tools from our agent_tools file
            config = types.GenerateContentConfig(
                system_instruction=sys_instruct,
                tools=AVAILABLE_TOOLS,
            )
            
            logger.info("Sending initial request to Gemini model", extra={"user_id": sub})
            start_time = time.time()
            response = await ai_client.aio.models.generate_content(
                model='gemini-3.1-flash-lite-preview',
                contents=genai_contents,
                config=config
            )
            duration = time.time() - start_time
            logger.info(f"Gemini API call completed", extra={"user_id": sub, "duration_s": round(duration, 2), "iteration": 0})
            
            iterations = 0
            while response.function_calls and iterations < 5:
                iterations += 1
                # Add model's tool calls to the history context
                genai_contents.append(response.candidates[0].content)
                
                function_response_parts = []
                for call in response.function_calls:
                    if call.name == "record_core_memory":
                        memory_text = call.args.get("memory_text")
                        if memory_text:
                            await save_core_memory(sub, memory_text)
                            logger.info("Tool executed: record_core_memory", extra={"user_id": sub, "memory_text": memory_text})
                            
                        function_response_parts.append(
                            types.Part.from_function_response(
                                name="record_core_memory",
                                response={"status": "success"}
                            )
                        )
                    elif call.name == "record_milestone":
                        milestone_text = call.args.get("milestone_text")
                        if milestone_text:
                            await save_milestone(sub, milestone_text)
                            logger.info("Tool executed: record_milestone", extra={"user_id": sub, "milestone_text": milestone_text})
                            
                        function_response_parts.append(
                            types.Part.from_function_response(
                                name="record_milestone",
                                response={"status": "success"}
                            )
                        )
                    elif call.name == "retrieve_core_memories":
                        max_results = call.args.get("max_results")
                        # cast max_results to int if it exists, since args might give a float
                        try:
                            max_results = int(max_results) if max_results is not None else None
                        except ValueError:
                            max_results = None
                        memories = await get_core_memories(sub, max_results)
                        logger.info("Tool executed: retrieve_core_memories", extra={"user_id": sub, "max_results": max_results})
                        function_response_parts.append(
                            types.Part.from_function_response(
                                name="retrieve_core_memories",
                                response={"memories": memories}
                            )
                        )
                    elif call.name == "retrieve_latest_core_memory":
                        memory = await get_latest_core_memory(sub)
                        logger.info("Tool executed: retrieve_latest_core_memory", extra={"user_id": sub})
                        function_response_parts.append(
                            types.Part.from_function_response(
                                name="retrieve_latest_core_memory",
                                response={"memory": memory}
                            )
                        )
                    elif call.name == "retrieve_milestones":
                        max_results = call.args.get("max_results")
                        try:
                            max_results = int(max_results) if max_results is not None else None
                        except ValueError:
                            max_results = None
                        milestones = await get_milestones(sub, max_results)
                        logger.info("Tool executed: retrieve_milestones", extra={"user_id": sub, "max_results": max_results})
                        function_response_parts.append(
                            types.Part.from_function_response(
                                name="retrieve_milestones",
                                response={"milestones": milestones}
                            )
                        )
                    elif call.name == "retrieve_latest_milestone":
                        milestone = await get_latest_milestone(sub)
                        logger.info("Tool executed: retrieve_latest_milestone", extra={"user_id": sub})
                        function_response_parts.append(
                            types.Part.from_function_response(
                                name="retrieve_latest_milestone",
                                response={"milestone": milestone}
                            )
                        )
                    elif call.name == "get_recent_workouts":
                        days_back = call.args.get("days_back", 7)
                        limit = call.args.get("limit", 10)
                        min_dist = call.args.get("min_distance_km")
                        max_dist = call.args.get("max_distance_km")
                        
                        try: days_back = int(days_back) if days_back is not None else 7
                        except (ValueError, TypeError): days_back = 7
                        try: limit = int(limit) if limit is not None else 10
                        except (ValueError, TypeError): limit = 10
                        try: min_dist = float(min_dist) if min_dist is not None else None
                        except (ValueError, TypeError): min_dist = None
                        try: max_dist = float(max_dist) if max_dist is not None else None
                        except (ValueError, TypeError): max_dist = None

                        workouts_str = await get_user_workouts_from_db(
                            user_id=sub, 
                            days_back=days_back, 
                            limit=limit, 
                            min_distance_km=min_dist, 
                            max_distance_km=max_dist
                        )
                        logger.info("Tool executed: get_recent_workouts", extra={"user_id": sub, "days_back": days_back, "limit": limit, "min_distance_km": min_dist, "max_distance_km": max_dist})
                        function_response_parts.append(
                            types.Part.from_function_response(
                                name="get_recent_workouts",
                                response={"workouts_summary": workouts_str}
                            )
                        )
                    elif call.name == "get_specific_workout":
                        activity_id = call.args.get("activity_id")
                        try:
                            activity_id = int(activity_id) if activity_id is not None else 0
                        except (ValueError, TypeError):
                            activity_id = 0
                            
                        workout_str = await get_specific_workout_from_db(
                            user_id=sub,
                            activity_id=activity_id
                        )
                        logger.info("Tool executed: get_specific_workout", extra={"user_id": sub, "activity_id": activity_id, "workout_details": workout_str})
                        function_response_parts.append(
                            types.Part.from_function_response(
                                name="get_specific_workout",
                                response={"workout_details": workout_str}
                            )
                        )
                    elif call.name == "update_workout_notes":
                        activity_id = call.args.get("activity_id")
                        notes = call.args.get("notes")
                        
                        try:
                            activity_id = int(activity_id) if activity_id is not None else 0
                        except (ValueError, TypeError):
                            activity_id = 0
                            
                        if activity_id and notes:
                            await update_workout_notes_in_db(sub, activity_id, notes)
                            logger.info("Tool executed: update_workout_notes", extra={"user_id": sub, "activity_id": activity_id, "notes": notes})
                            
                        function_response_parts.append(
                            types.Part.from_function_response(
                                name="update_workout_notes",
                                response={"status": "success"}
                            )
                        )
                    elif call.name == "set_training_directive":
                        focus = call.args.get("focus")
                        rationale = call.args.get("rationale")
                        target_date = call.args.get("target_date")
                        
                        if focus and rationale and target_date:
                            await set_training_directive_in_db(sub, focus, rationale, target_date)
                            logger.info("Tool executed: set_training_directive", extra={"user_id": sub, "focus": focus, "rationale": rationale, "target_date": target_date})
                            
                        function_response_parts.append(
                            types.Part.from_function_response(
                                name="set_training_directive",
                                response={"status": "success"}
                            )
                        )
                    elif call.name == "remove_training_directive":
                        focus = call.args.get("focus")
                        
                        if focus:
                            await remove_training_directive_from_db(sub, focus)
                            logger.info("Tool executed: remove_training_directive", extra={"user_id": sub, "focus": focus})
                            
                        function_response_parts.append(
                            types.Part.from_function_response(
                                name="remove_training_directive",
                                response={"status": "success"}
                            )
                        )
                    elif call.name == "get_training_directives":
                        status = call.args.get("status", "active")
                        
                        directives_str = await get_training_directives_from_db(sub, status)
                        logger.info("Tool executed: get_training_directives", extra={"user_id": sub, "status": status})
                        
                        function_response_parts.append(
                            types.Part.from_function_response(
                                name="get_training_directives",
                                response={"directives": directives_str}
                            )
                        )
                    elif call.name == "update_biometrics":
                        args = call.args
                        height = args.get("height_cm")
                        weight = args.get("weight_kg")
                        birth_yr = args.get("birth_year")
                        max_hr = args.get("max_hr")
                        resting_hr = args.get("resting_hr")
                        thresh_hr = args.get("threshold_hr")
                        sex = args.get("sex")
                        
                        await update_user_biometrics_in_db(
                            sub,
                            height_cm=height,
                            weight_kg=weight,
                            birth_year=birth_yr,
                            max_hr=max_hr,
                            resting_hr=resting_hr,
                            threshold_hr=thresh_hr,
                            sex=sex
                        )
                        logger.info("Tool executed: update_biometrics", extra={
                            "user_id": sub,
                            "height_cm": height,
                            "weight_kg": weight,
                            "birth_year": birth_yr,
                            "max_hr": max_hr,
                            "resting_hr": resting_hr,
                            "threshold_hr": thresh_hr,
                            "sex": sex
                        })
                        
                        function_response_parts.append(
                            types.Part.from_function_response(
                                name="update_biometrics",
                                response={"status": "success"}
                            )
                        )
                    elif call.name == "get_biometrics":
                        bio_str = await get_user_biometrics_from_db(sub)
                        logger.info("Tool executed: get_biometrics", extra={"user_id": sub})
                        
                        function_response_parts.append(
                            types.Part.from_function_response(
                                name="get_biometrics",
                                response={"biometrics": bio_str}
                            )
                        )
                
                genai_contents.append(types.Content(role="function", parts=function_response_parts))
                
                # Resubmit with function results to get final conversational response
                logger.info(f"Resubmitting to Gemini model with tool responses", extra={"user_id": sub, "iteration": iterations})
                start_time = time.time()
                response = await ai_client.aio.models.generate_content(
                    model='gemini-3.1-flash-lite-preview',
                    contents=genai_contents,
                    config=config
                )
                duration = time.time() - start_time
                logger.info(f"Gemini API tool resubmission completed", extra={"user_id": sub, "duration_s": round(duration, 2), "iteration": iterations})
                
            bot_text = response.text or "I'm sorry, I couldn't generate a response."
            messages.append({"role": "assistant", "content": bot_text})
        except Exception as e:
            logger.error(f"Error calling Gemini: {e}")
            messages.append({"role": "assistant", "content": "Sorry, I am facing technical difficulties connecting to my cognitive cores."})
    else:
        # Mock assistant response fallback
        messages.append({"role": "assistant", "content": f"AI Client unavailable. You have {len(messages)//2} exchanges so far."})
    
    # Save back to database
    await db.put(f"users/{sub}/chat_sessions", "current_session", {"messages": messages}, merge=True)
    
    logger.info("Chat message processed", request=request, extra={
        "user_id": sub,
        "first_name": first_name,
        "persona": persona.name,
        "message_count": len(messages),
        "new_message": payload.message
    })
    
    return {"status": "ok", "messages": messages, "context_loaded": True}

@router.get("/chat/history")
async def get_chat_history(user: dict = Depends(get_current_user)):
    sub = user.get("sub")
    session_data = await db.get(f"users/{sub}/chat_sessions", "current_session")
    messages = session_data.get("messages", []) if session_data else []
    return {"status": "ok", "messages": messages}
