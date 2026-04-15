from fastapi import APIRouter, Request
from src.core.logger import logger
from .models import WebhookPayload

router = APIRouter()

@router.post("/webhook")
async def receive_webhook(request: Request):
    logger.info("Received webhook", request=request)
    return {"status": "ok", "message": "webhook received"}
