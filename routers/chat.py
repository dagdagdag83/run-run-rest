from fastapi import APIRouter, Request, Depends
from google.genai import types
from models import ChatPayload
from personas import get_persona
from dependencies import db, ai_client, get_current_user
from logger import logger

router = APIRouter()

@router.post("/chat")
async def chat_interaction(payload: ChatPayload, request: Request, user: dict = Depends(get_current_user)):
    sub = user.get("sub")
    first_name = user.get("given_name") or user.get("name", "User")
    selected_persona_id = user.get("selected_persona", "supportive-realist")
    
    persona = get_persona(selected_persona_id)
    
    session_data = await db.get(f"users/{sub}/chat_sessions", "current_session")
    if not session_data:
        session_data = {"messages": []}
        
    messages = session_data.get("messages", [])
    
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
                
            sys_instruct = f"The user's name is {first_name}.\n{persona.system_prompt}"
            
            response = await ai_client.aio.models.generate_content(
                model='gemini-3.1-flash-lite-preview',
                contents=genai_contents,
                config=types.GenerateContentConfig(
                    system_instruction=sys_instruct,
                )
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
