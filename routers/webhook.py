from fastapi import APIRouter, Request
from pydantic import BaseModel
from logger import logger

router = APIRouter()

class WebhookPayload(BaseModel):
    pass  # To be defined

@router.post("/webhook")
async def receive_webhook(request: Request):
    logger.info("Received webhook", request=request)
    return {"status": "ok", "message": "webhook received"}
