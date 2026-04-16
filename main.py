import os
from dotenv import load_dotenv

load_dotenv(override=True)

from fastapi import FastAPI
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware

from src.features.auth import router as auth_router
from src.features.chat import router as chat_router
from src.features.strava import router as strava_router

app = FastAPI(title="Run-Run-Rest", description="Agentic Fitness Harness")
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.environ.get("SESSION_SECRET_KEY", "fallback-secret"),
    same_site="lax",  # Set to 'lax' to avoid cross-origin redirect state mismatch issues in production
    https_only=os.environ.get("ENVIRONMENT") == "production"
)

app.include_router(auth_router.router)
app.include_router(chat_router.router)
app.include_router(strava_router.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/", response_class=FileResponse)
async def get_root():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    port = 8000 if os.environ.get("ENVIRONMENT") == "production" else 80
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
