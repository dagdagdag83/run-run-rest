from datetime import datetime, timezone, timedelta
from src.shared.dependencies import db
from src.shared.logger import logger

recall_past_conversation_tool = {
    "function_declarations": [
        {
            "name": "recall_past_conversation",
            "description": "Use this tool to query histerical chat logs with the user whenever they refer to older conversations or advice given outside your active context window (older than 7 days). It uses a cheaper, fast sub-agent to review the chat logs and summarize relevance.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "topic": {
                        "type": "STRING",
                        "description": "The specific topic, advice, or agreement you are looking for."
                    },
                    "approximate_days_ago": {
                        "type": "INTEGER",
                        "description": "Approximate number of days ago this was discussed. Uses a fuzzy +/- 15 day window."
                    }
                },
                "required": ["topic", "approximate_days_ago"]
            }
        }
    ]
}

def prune_chat_context(messages: list, days: int = 7) -> list:
    """Takes a list of messages and filters out those older than 'days' from now."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    
    pruned = []
    thread_is_active = True  # We assume recent until proven old

    import re
    date_pattern = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]")

    for msg in messages:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            match = date_pattern.search(content)
            if match:
                date_str = match.group(1)
                try:
                    msg_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                    thread_is_active = msg_time >= cutoff
                except ValueError:
                    thread_is_active = True
            else:
                thread_is_active = True
                
        if thread_is_active:
            pruned.append(msg)
            
    return pruned

def get_fuzzy_time_window(approximate_days_ago: int) -> tuple[datetime, datetime]:
    target_date = datetime.now(timezone.utc) - timedelta(days=approximate_days_ago)
    return target_date - timedelta(days=15), target_date + timedelta(days=15)

async def fetch_historical_chat(user_id: str, start_date: datetime, end_date: datetime) -> str:
    try:
        doc = await db.get(f"users/{user_id}/chat_sessions", "current_session")
        if not doc:
            return "No historical chat data found."
            
        messages = doc.get("messages", [])
        if not messages:
            return "No historical chat data found."
            
        import re
        date_pattern = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]")
        
        filtered_lines = []
        keep_thread = False
        
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "user":
                match = date_pattern.search(content)
                if match:
                    date_str = match.group(1)
                    try:
                        msg_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                        keep_thread = start_date <= msg_time <= end_date
                    except ValueError:
                        keep_thread = False
                else:
                    keep_thread = False
                    
            if keep_thread:
                speaker = "User" if role == "user" else "Coach"
                # Remove the timestamp from the start for cleaner reading, optional
                clean_content = re.sub(r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}\]\s*", "", content) if role == "user" else content
                filtered_lines.append(f"{speaker}: {clean_content}")
                
        if not filtered_lines:
            return "No messages found in that time frame."
            
        return "\n".join(filtered_lines)
    except Exception as e:
        logger.error(f"Unexpected error fetching historical chat for {user_id}: {e}")
        return f"System Error: {e}"

async def summarize_past_chat(raw_chat_log: str, search_topic: str) -> str:
    import google.genai as genai
    from google.genai import types
    import os
    
    if raw_chat_log in ("No historical chat data found.", "No messages found in that time frame.") or raw_chat_log.startswith("System Error:"):
        return raw_chat_log
        
    try:
        from src.shared.dependencies import ai_client
        if not ai_client:
             return "System Error: AI client not available for Librarian."
             
        sys_instruct = f"You are a librarian sub-agent. Review the provided chat history. Extract and summarize any discussions, advice, or agreements related specifically to: '{search_topic}'. Return a single, dense paragraph. If the topic is not found, reply exactly with 'No relevant discussion found in this time frame.'"
        
        response = await ai_client.aio.models.generate_content(
            model='gemini-3.1-flash-lite-preview',
            contents=raw_chat_log,
            config=types.GenerateContentConfig(
                system_instruction=sys_instruct,
                temperature=0.2
            )
        )
        return response.text or "Summary generation failed."
    except Exception as e:
        logger.error(f"Librarian summarization failed: {e}")
        return f"System Error summarizing chat: {e}"

async def recall_past_conversation(user_id: str, topic: str, approximate_days_ago: int) -> str:
    start_date, end_date = get_fuzzy_time_window(approximate_days_ago)
    logger.info("Spawning Librarian sub-agent for RAG", extra={
        "user_id": user_id, 
        "search_topic": topic, 
        "search_range_start": start_date.isoformat(),
        "search_range_end": end_date.isoformat()
    })
    raw_log = await fetch_historical_chat(user_id, start_date, end_date)
    result = await summarize_past_chat(raw_log, topic)
    logger.info("Librarian sub-agent completed", extra={
        "user_id": user_id,
        "search_topic": topic,
        "result_length": len(result),
        "result": result
    })
    return result
