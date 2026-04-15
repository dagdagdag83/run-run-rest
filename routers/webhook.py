from fastapi import APIRouter, Request
from pydantic import BaseModel
from logger import logger

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
    return {"status": "ok", "message": "webhook received"}
