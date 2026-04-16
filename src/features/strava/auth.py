import os
import time
import httpx
from src.shared.logger import logger
from src.shared.dependencies import db

async def get_valid_strava_token(user_id: str) -> str | None:
    """
    Retrieves a valid Strava access token for the given user, refreshing it if necessary.
    Returns None if the user does not have Strava configured or an error occurs.
    """
    try:
        user_data = await db.get("users", user_id)
        if not user_data:
            logger.warning(f"User {user_id} not found in DB.")
            return None

        access_token = user_data.get("strava_access_token")
        refresh_token = user_data.get("strava_refresh_token")
        expires_at = user_data.get("strava_expires_at")

        if not access_token or not refresh_token or not expires_at:
            logger.info(f"Strava credentials incomplete or missing for user {user_id}.")
            return None

        # Check if expiration is within the next 1 hour (3600 seconds)
        current_time = int(time.time())
        if int(expires_at) - current_time > 3600:
            logger.info(f"Strava token for user {user_id} is valid.")
            return access_token

        logger.info(f"Strava token for user {user_id} is expired or expiring soon. Refreshing...")
        client_id = os.environ.get("STRAVA_CLIENT_ID")
        client_secret = os.environ.get("STRAVA_CLIENT_SECRET")

        if not client_id or not client_secret:
            logger.error("STRAVA_CLIENT_ID or STRAVA_CLIENT_SECRET not configured in environment.")
            return None

        url = "https://www.strava.com/oauth/token"
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, data=payload)
            resp.raise_for_status()
            token_data = resp.json()

            new_access_token = token_data.get("access_token")
            new_refresh_token = token_data.get("refresh_token")
            new_expires_at = token_data.get("expires_at")

            if not new_access_token or not new_expires_at:
                logger.error("Invalid response from Strava token refresh: Missing expected token keys")
                return None

            update_data = {
                "strava_access_token": new_access_token,
                "strava_expires_at": new_expires_at
            }
            if new_refresh_token:
                update_data["strava_refresh_token"] = new_refresh_token

            await db.put("users", user_id, update_data, merge=True)
            logger.info(f"Successfully refreshed and saved Strava token for user {user_id}.")

            return new_access_token

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during Strava token refresh for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting Strava token for user {user_id}: {e}")
        return None
