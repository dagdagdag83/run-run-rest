import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
import httpx

# We must mock environment to avoid dependencies loading wrong db natively
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill Strava Activities")
    parser.add_argument("--env", choices=["local", "prod"], required=True)
    parser.add_argument("--days-back", type=int, default=None)
    args = parser.parse_args()
    
    os.environ["ENVIRONMENT"] = "production" if args.env == "prod" else "local"

from dotenv import load_dotenv
load_dotenv(override=True)

# Now import dependencies safely
from src.shared.logger import logger
from src.shared.dependencies import db
from src.features.strava.auth import get_valid_strava_token
from src.features.strava.parser import transform_strava_activity
from src.features.strava.weather import enrich_with_weather
from src.features.strava.physiology.enrichment import enrich_with_physiology
from src.features.strava.scout.assessment import enrich_with_scout_assessment

TARGET_USER_ID = "368456321882196914"

def parse_rate_limits(headers):
    """Returns (15m_usage, daily_usage, 15m_limit, daily_limit) or Nones"""
    usage = headers.get("X-RateLimit-Usage")
    limit = headers.get("X-RateLimit-Limit")
    
    if usage and limit:
        try:
            u_15, u_day = map(int, usage.split(","))
            l_15, l_day = map(int, limit.split(","))
            return u_15, u_day, l_15, l_day
        except ValueError:
            pass
    return None, None, None, None

async def check_rate_limits(headers):
    u_15, u_day, l_15, l_day = parse_rate_limits(headers)
    if u_15 is None:
        return
        
    logger.info(f"Rate limits - 15m: {u_15}/{l_15}, Daily: {u_day}/{l_day}")
    
    if u_day >= l_day:
        logger.error(f"Daily rate limit reached ({u_day}/{l_day}). Aborting completely.")
        sys.exit(1)
        
    if u_15 >= (l_15 - 5): # Leave 5 requests buffer
        logger.warning(f"15-minute rate limit approached ({u_15}/{l_15}). Sleeping for 15 minutes...")
        await asyncio.sleep(900)
        logger.info("Resuming after 15-minute sleep.")

async def run_backfill(days_back: int = None):
    logger.info(f"Starting strava backfill for user {TARGET_USER_ID}")
    token = await get_valid_strava_token(TARGET_USER_ID)
    if not token:
        logger.error("Failed to get valid Strava token.")
        sys.exit(1)
        
    headers = {"Authorization": f"Bearer {token}"}
    params = {"per_page": 200, "page": 1}
    
    if days_back:
        after_dt = datetime.now(timezone.utc) - timedelta(days=days_back)
        params["after"] = int(after_dt.timestamp())
        
    async with httpx.AsyncClient(timeout=60.0) as client:
        while True:
            logger.info(f"Fetching activities page {params['page']}")
            resp = await client.get("https://www.strava.com/api/v3/athlete/activities", headers=headers, params=params)
            
            await check_rate_limits(resp.headers)
            resp.raise_for_status()
            
            activities = resp.json()
            if not activities:
                logger.info("No more activities found.")
                break
                
            for activity in activities:
                object_id = activity.get("id")
                sport_type = activity.get("sport_type") or activity.get("type", "Unknown")
                
                allowed_types = ["Run", "TrailRun", "VirtualRun", "Walk", "Hike"]
                if sport_type not in allowed_types:
                    continue
                    
                # Check Idempotency
                parsed_collection_path = f"users/{TARGET_USER_ID}/workouts"
                existing_doc = await db.get(collection=parsed_collection_path, doc_id=str(object_id))
                if existing_doc:
                    logger.info(f"Activity {object_id} already exists in DB. Skipping.")
                    continue
                    
                # Wait before detail fetch to be friendly? The rate limit check handles it, but let's just fetch
                detail_url = f"https://www.strava.com/api/v3/activities/{object_id}"
                logger.info(f"Fetching detail view for activity {object_id} type {sport_type}")
                detail_resp = await client.get(detail_url, headers=headers)
                
                await check_rate_limits(detail_resp.headers)
                
                try:
                    detail_resp.raise_for_status()
                except httpx.HTTPStatusError as e:
                    logger.error(f"Failed to fetch detail for {object_id}: {e}")
                    if detail_resp.status_code == 404:
                        continue
                    else:
                        raise
                
                activity_data = detail_resp.json()
                
                # Save Raw
                raw_collection_path = f"users/{TARGET_USER_ID}/raw_strava_activities"
                await db.put(collection=raw_collection_path, doc_id=str(object_id), data=activity_data)
                
                # Enrichment Pipeline
                weather_data = await enrich_with_weather(activity_data)
                transformed_data = transform_strava_activity(activity_data)
                if weather_data:
                    transformed_data["weather"] = weather_data
                    
                physiology_data = await enrich_with_physiology(TARGET_USER_ID, transformed_data)
                if physiology_data:
                    transformed_data["metrics"] = physiology_data
                    
                scout_summary = await enrich_with_scout_assessment(transformed_data)
                if scout_summary:
                    transformed_data["auto_assessment"] = scout_summary
                    
                # Save Parsed
                await db.put(collection=parsed_collection_path, doc_id=str(object_id), data=transformed_data)
                logger.info(f"Successfully processed and saved activity {object_id}")
                
            params["page"] += 1

if __name__ == "__main__":
    if args.env == "prod":
        logger.info("Initializing in PRODUCTION mode.")
    else:
        logger.info("Initializing in LOCAL mode.")
        
    asyncio.run(run_backfill(args.days_back))
