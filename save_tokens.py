import asyncio
from storage import FirestoreStorage

async def main():
    #db = FirestoreStorage(database="run-run-rest-main-db")
    # Actually wait we need to use the one from dependencies or what?
    # the existing dependencies.py initializes db based on environment.
    from dependencies import db
    
    await db.put("users", "368456321882196914", {
        "strava_access_token": "21706ce20841ea501ea3822269df053475a8934b",
        "strava_refresh_token": "a98a3599ceac3baeb345f4bfa9b3f9e7338f69ff",
        "strava_expires_at": 1776345767
    }, merge=True)
    
    doc = await db.get("users", "368456321882196914")
    print("Saved:", doc)

if __name__ == "__main__":
    asyncio.run(main())
