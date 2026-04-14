import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware

from src.core.auth.router import router as auth_router
from src.features.chat.router import router as chat_router
from src.features.webhook.router import router as webhook_router

app = FastAPI(title="Run-Run-Rest", description="Agentic Fitness Harness")
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.environ.get("SESSION_SECRET_KEY", "fallback-secret"),
    same_site="lax",  # Set to 'lax' to avoid cross-origin redirect state mismatch issues in production
    https_only=os.environ.get("ENVIRONMENT") == "production"
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(webhook_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/", response_class=FileResponse)
async def get_root():
    return FileResponse("src/static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
