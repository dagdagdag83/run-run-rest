from fastapi import FastAPI, Request
from pydantic import BaseModel
from pythonjsonlogger import json
import logging

# Setup JSON logger for stdout (GCP compatible)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logHandler = logging.StreamHandler()
formatter = json.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

app = FastAPI(title="Run-Run-Rest", description="Agentic Fitness Harness")

class WebhookPayload(BaseModel):
    pass  # To be defined

class ChatPayload(BaseModel):
    pass  # To be defined

@app.post("/webhook")
async def receive_webhook(request: Request):
    logger.info("Received webhook")
    return {"status": "ok", "message": "webhook received"}

@app.post("/chat")
async def chat_interaction(request: Request):
    logger.info("Received chat interaction")
    return {"status": "ok", "response": "mock response"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
