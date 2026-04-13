import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
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
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SESSION_SECRET_KEY", "fallback-secret"))

oauth = OAuth()
oauth.register(
    name='zitadel',
    server_metadata_url=os.environ.get('ZITADEL_DISCOVERY_URL'),
    client_id=os.environ.get('ZITADEL_CLIENT_ID'),
    client_secret=os.environ.get('ZITADEL_CLIENT_SECRET'),
    client_kwargs={'scope': 'openid profile email'},
)

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

@app.get("/", response_class=FileResponse)
async def get_root():
    return FileResponse("static/index.html")

@app.get("/login")
async def login(request: Request):
    # request.url_for generates an absolute URL based on the current request
    redirect_uri = request.url_for('auth_callback')
    return await oauth.zitadel.authorize_redirect(request, str(redirect_uri))

@app.get("/auth/callback")
async def auth_callback(request: Request):
    token = await oauth.zitadel.authorize_access_token(request)
    logger.info(f"Zitadel OAuth Token Received: {token}")
    user = token.get('userinfo')
    logger.debug(f"Zitadel Userinfo: {user}")
    if user:
        request.session['user'] = user
    return RedirectResponse(url='/')

@app.get("/logout")
async def logout(request: Request):
    request.session.pop('user', None)
    
    metadata = await oauth.zitadel.load_server_metadata()
    end_session_endpoint = metadata.get('end_session_endpoint')
    if end_session_endpoint:
        # Redirect to IDP logout with optional post_logout_redirect_uri (depends on OIDC compliance, but standard enough)
        # Authlib doesn't have a direct helper for this in Starlette integration without extra params, so we manually redirect
        post_logout_uri = str(request.url_for('auth_logout_callback'))
        return RedirectResponse(url=f"{end_session_endpoint}?post_logout_redirect_uri={post_logout_uri}")
    
    return RedirectResponse(url='/')

@app.get("/auth/logout/callback")
async def auth_logout_callback(request: Request):
    return RedirectResponse(url='/')

@app.get("/api/me")
async def api_me(request: Request):
    user = request.session.get('user')
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    return {"user": user}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
