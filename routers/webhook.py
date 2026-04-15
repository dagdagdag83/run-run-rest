import os
import httpx
from fastapi import APIRouter, Request
from pydantic import BaseModel
from logger import logger
from dependencies import db

router = APIRouter()

class WebhookPayload(BaseModel):
    pass  # To be defined

@router.get("/webhook")
async def validate_webhook(request: Request):
    # Blindly echo the Strava challenge to keep the webhook alive forever.
    challenge = request.query_params.get("hub.challenge")
    if challenge:
        return {"hub.challenge": challenge}
    else:
        return {"error": "Something missing..."}

@router.post("/webhook")
async def receive_webhook(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = await request.body()
    logger.info(f"Webhook POST received. Body: {body}")
    
    if isinstance(body, dict) and body.get("object_type") == "activity":
        object_id = body.get("object_id")
        if object_id:
            logger.info(f"Processing activity: {object_id}")
            token = os.environ.get("STRAVA_API_TOKEN")
            if token:
                url = f"https://www.strava.com/api/v3/activities/{object_id}"
                headers = {"Authorization": f"Bearer {token}"}
                
                async with httpx.AsyncClient() as client:
                    try:
                        resp = await client.get(url, headers=headers)
                        resp.raise_for_status()
                        activity_data = resp.json()
                        user_id = "368456321882196914"
                        collection_path = f"users/{user_id}/raw_strava_activities"
                        await db.put(collection=collection_path, doc_id=str(object_id), data=activity_data)
                        logger.info(f"Saved activity {object_id} to Firestore")
                    except Exception as e:
                        logger.error(f"Error fetching/saving activity {object_id}: {e}")
            else:
                logger.warning("STRAVA_API_TOKEN is not set")

    return {"status": "ok", "message": "webhook received"}
