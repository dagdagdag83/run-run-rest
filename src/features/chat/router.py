from fastapi import APIRouter, Request, Depends
from google.genai import types
from src.features.chat.models import ChatPayload
from src.features.chat.personas import get_persona, build_system_prompt
from src.shared.dependencies import db, ai_client, get_current_user
from src.shared.logger import logger
from src.features.chat.registry import AVAILABLE_TOOLS, execute_tool
from src.features.chat.librarian.tools import prune_chat_context
from src.features.chat.constants import ANCHOR_PROMPT
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
    logger.info("Persona chosen for interaction", extra={"user_id": sub, "persona_id": persona.id})
    
    # Query for active training block
    active_block_str = "No active training block set. Proactively discuss setting one."
    try:
        from google.cloud import firestore as firestore_module
        if hasattr(db, '_db'):
            collection_ref = db._db.collection(f"users/{sub}/training_blocks")
            active_docs = await collection_ref.where(filter=firestore_module.FieldFilter("status", "==", "active")).limit(1).get()
            if active_docs:
                d = active_docs[0].to_dict()
                block_parts = [
                    f"Phase Name: {d.get('phase_name', 'Unnamed')}",
                    f"Target Date: {d.get('target_date', 'N/A')}",
                    f"Primary Target: {d.get('primary_target', 'N/A')}"
                ]
                sec = d.get('secondary_targets', [])
                if sec:
                    block_parts.append(f"Secondary Targets: {', '.join(sec)}")
                habits = d.get('maintenance_habits', [])
                if habits:
                    block_parts.append(f"Maintenance Habits: {', '.join(habits)}")
                active_block_str = "\n".join(block_parts)
    except Exception as e:
        logger.error(f"Error fetching active training block for {sub}: {e}")
    
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
            # Step 1: The Sliding Window (Context Pruning)
            messages_to_process = prune_chat_context(messages, days=7)
            
            genai_contents = []
            for i, msg in enumerate(messages_to_process):
                role = "model" if msg["role"] == "assistant" else msg["role"]
                
                text_content = msg["content"]
                # Intercept the payload: append ANCHOR_PROMPT to the final user message
                if i == len(messages_to_process) - 1 and role == "user":
                    text_content += ANCHOR_PROMPT
                    
                genai_contents.append(
                    types.Content(role=role, parts=[types.Part.from_text(text=text_content)])
                )
                
            biometrics = user.get("biometrics")
            if biometrics:
                biometrics_parts = []
                for k, v in biometrics.items():
                    biometrics_parts.append(f"{k.replace('_', ' ').title()}: {v}")
                biometrics_str = " | ".join(biometrics_parts)
            else:
                biometrics_str = "No specific biometrics recorded."

            sys_instruct = build_system_prompt(persona, first_name, current_timestamp, active_directives_str, biometrics_str, active_block_str)
            logger.info("System prompt generated", extra={"user_id": sub, "prompt_length": len(sys_instruct)})
            
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
                    resp_part = await execute_tool(call, sub)
                    function_response_parts.append(resp_part)
                
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
