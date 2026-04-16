import os
import httpx
from fastapi import APIRouter, Request
from pydantic import BaseModel
from logger import logger
from dependencies import db
from src.features.strava.auth import get_valid_strava_token
from src.features.strava.parser import transform_strava_activity

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
    logger.info(f"Webhook POST received. Body: {body} (Type: {type(body)})")
    
    if isinstance(body, dict) and body.get("object_type") == "activity":
        object_id = body.get("object_id")
        logger.info(f"Parsed activity object_id: {object_id}")
        if object_id:
            user_id = "368456321882196914"
            token = await get_valid_strava_token(user_id)
            if token:
                logger.info(f"Valid Strava token retrieved for user {user_id}, fetching activity: {object_id}")
                url = f"https://www.strava.com/api/v3/activities/{object_id}"
                headers = {"Authorization": f"Bearer {token}"}
                
                async with httpx.AsyncClient() as client:
                    try:
                        resp = await client.get(url, headers=headers)
                        logger.info(f"Strava API Response Status: {resp.status_code}")
                        resp.raise_for_status()
                        activity_data = resp.json()
                        
                        sport_type = activity_data.get("sport_type") or activity_data.get("type", "Unknown")
                        allowed_types = ["Run", "TrailRun", "VirtualRun", "Walk", "Hike"]
                        
                        if sport_type not in allowed_types:
                            logger.info(f"Skipping non-running activity {object_id} of type {sport_type}")
                            return {"status": "ok", "message": "skipped non-running task"}
                            
                        collection_path = f"users/{user_id}/raw_strava_activities"
                        logger.info(f"Attempting to db.put to collection {collection_path} with id {object_id}")
                        await db.put(collection=collection_path, doc_id=str(object_id), data=activity_data)
                        logger.info(f"Saved activity {object_id} to Firestore (or fallback Storage)")
                        
                        # Verify the db put worked
                        check = await db.get(collection=collection_path, doc_id=str(object_id))
                        if check:
                            logger.info(f"Verified raw {object_id} exists via db.get()")
                        else:
                            logger.error(f"Failed db.get() check for raw {object_id}!")
                            
                        # Now parse and store the LLM-friendly version
                        from src.features.strava.weather import enrich_with_weather
                        from src.features.physiology.enrichment import enrich_with_physiology
                        weather_data = await enrich_with_weather(activity_data)
                        
                        transformed_data = transform_strava_activity(activity_data)
                        if weather_data:
                            transformed_data["weather"] = weather_data
                            
                        # Add physiological enrichment
                        physiology_data = await enrich_with_physiology(user_id, transformed_data)
                        if physiology_data:
                            transformed_data["metrics"] = physiology_data
                            
                        parsed_collection_path = f"users/{user_id}/workouts"
                        await db.put(collection=parsed_collection_path, doc_id=str(object_id), data=transformed_data)
                        logger.info(f"Saved parsed activity {object_id} to {parsed_collection_path} with weather and physiology enrichment")
                            
                    except httpx.HTTPStatusError as e:
                        logger.error(f"Strava HTTPStatusError for {object_id}: {e.response.status_code} - {e.response.text}")
                    except Exception as e:
                        logger.error(f"Error fetching/saving activity {object_id}: {e}")
            else:
                logger.warning(f"Could not obtain a valid Strava token for user {user_id}")
    else:
        logger.info(f"Ignored webhook. Not a valid activity dict. IS_DICT: {isinstance(body, dict)}")

    return {"status": "ok", "message": "webhook received"}

