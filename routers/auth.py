import os
import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from dependencies import oauth, db
from logger import logger

router = APIRouter()

@router.get("/login")
async def login(request: Request):
    # request.url_for generates an absolute URL based on the current request
    redirect_uri = request.url_for('auth_callback')
    return await oauth.zitadel.authorize_redirect(request, str(redirect_uri))

@router.get("/auth/callback")
async def auth_callback(request: Request):
    token = await oauth.zitadel.authorize_access_token(request)
    logger.info("Zitadel OAuth Token Received", request=request, extra={"token": token})
    
    # Authlib automatically cryptographically verifies and decodes the `id_token` 
    # during `authorize_access_token` and maps the claims into the 'userinfo' dictionary key.
    # This is purely local and does NOT trigger a redundant network call!
    id_token_claims = token.get('userinfo')
    logger.debug("Decoded ID Token Claims", request=request, extra={"claims": id_token_claims})
    
    if id_token_claims:
        request.session['user'] = id_token_claims
        user_id = id_token_claims.get('sub')
        if user_id:
            logger.info("Upserting user into storage", request=request, extra={"user_id": user_id})
            
            # Check for existing structure to conditionally add defaults
            existing_user = await db.get("users", user_id)
            data = id_token_claims.copy()
            
            if not existing_user:
                data["selected_persona"] = "supportive-realist"
                data["active_goals"] = []
                
            # Upsert using set(..., merge=True) mechanics
            await db.put("users", user_id, data, merge=True)

    return RedirectResponse(url='/')

@router.get("/logout")
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

@router.get("/dump-cookie")
async def dump_cookie(request: Request):
    # This renders the exact raw cookie string the browser is sending
    return {"session_cookie": request.cookies.get("session")}

@router.get("/auth/logout/callback")
async def auth_logout_callback(request: Request):
    return RedirectResponse(url='/')

@router.get("/api/me")
async def api_me(request: Request):
    user = request.session.get('user')
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    return {"user": user}

@router.get("/strava/authorize")
async def strava_authorize():
    if os.environ.get("ENVIRONMENT") == "production":
        raise HTTPException(status_code=403, detail="Local fallback endpoint not available in production")
    
    client_id = "225274"
    redirect_uri = "http://localhost/exchange_token"
    url = f"http://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&approval_prompt=force&scope=read,activity:read"
    return RedirectResponse(url=url)

@router.get("/exchange_token")
async def exchange_token(code: str):
    if os.environ.get("ENVIRONMENT") == "production":
        raise HTTPException(status_code=403, detail="Local fallback endpoint not available in production")
        
    client_id = "225274"
    client_secret = "d92796701f97c01677178769ddf8233108aa11a7"
    
    async with httpx.AsyncClient() as client:
        resp = await client.post("https://www.strava.com/oauth/token", data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code"
        })
        resp.raise_for_status()
        token_data = resp.json()
        
    user_id = "368456321882196914"
    update_data = {
        "strava_access_token": token_data.get("access_token"),
        "strava_refresh_token": token_data.get("refresh_token"),
        "strava_expires_at": token_data.get("expires_at")
    }
    
    await db.put("users", user_id, update_data, merge=True)
    return {"message": "Success! Strava tokens updated.", "token_data": token_data}
