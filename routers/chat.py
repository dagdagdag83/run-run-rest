from fastapi import APIRouter, Request, Depends
from google.genai import types
from models import ChatPayload
from personas import get_persona, build_system_prompt
from dependencies import db, ai_client, get_current_user
from logger import logger
from agent_tools import (
    AVAILABLE_TOOLS, 
    save_core_memory, save_milestone,
    get_core_memories, get_latest_core_memory,
    get_milestones, get_latest_milestone
)
from datetime import datetime, timezone

router = APIRouter()

@router.post("/chat")
async def chat_interaction(payload: ChatPayload, request: Request, user: dict = Depends(get_current_user)):
    sub = user.get("sub")
    first_name = user.get("given_name") or user.get("name", "User")
    selected_persona_id = user.get("selected_persona", "supportive-realist")
    active_goals = user.get("active_goals", [])
    
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
                
            sys_instruct = build_system_prompt(persona, first_name, current_timestamp, active_goals)
            
            # Build config using tools from our agent_tools file
            config = types.GenerateContentConfig(
                system_instruction=sys_instruct,
                tools=AVAILABLE_TOOLS,
            )
            
            response = await ai_client.aio.models.generate_content(
                model='gemini-3.1-flash-lite-preview',
                contents=genai_contents,
                config=config
            )
            
            if response.function_calls:
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
                        logger.info("Tool executed: retrieve_core_memories", extra={"user_id": sub})
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
                        logger.info("Tool executed: retrieve_milestones", extra={"user_id": sub})
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
                
                genai_contents.append(types.Content(role="function", parts=function_response_parts))
                
                # Resubmit with function results to get final conversational response
                response = await ai_client.aio.models.generate_content(
                    model='gemini-3.1-flash-lite-preview',
                    contents=genai_contents,
                    config=config
                )
                
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
