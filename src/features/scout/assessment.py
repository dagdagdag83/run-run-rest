import json
from google.genai import Client
from logger import logger

SCOUT_PROMPT = """
You are a clinical sports data scientist analyzing a runner's workout JSON. Your job is anomaly detection and physiological insight. 

Do not summarize basic stats (total distance/time). Instead, identify the most significant physiological or environmental insights from the data. Scan for:
* Pacing strategy (e.g., negative splits, blowing up early, erratic speed).
* Cardiac drift (e.g., HR rising significantly while pace remains flat).
* Intensity mismatches (e.g., HR zone is much higher than expected for the pace).
* Environmental impact (e.g., how high winds or freezing temps likely affected the effort).

Output 2 to 4 concise, purely analytical sentences focusing ONLY on the highest-signal observations. If the run was perfectly steady and unremarkable, state that the metrics were stable. No markdown, no greetings, no fluff.
"""

async def enrich_with_scout_assessment(fully_enriched_data: dict) -> str | None:
    activity_id = fully_enriched_data.get("id")
    try:
        logger.info("Starting Scout auto-assessment", extra={"activity_id": activity_id, "distance": fully_enriched_data.get("distance")})
        compact_json = json.dumps(fully_enriched_data)
        client = Client(vertexai=True)
        response = await client.aio.models.generate_content(
            model='gemini-3.1-flash-lite-preview',
            contents=[SCOUT_PROMPT, compact_json]
        )
        logger.info("Scout auto-assessment completed successfully", extra={"activity_id": activity_id, "response": response.text})
        return response.text
    except Exception as e:
        logger.error(f"Scout assessment failed: {e}", extra={"activity_id": activity_id, "error": str(e)})
        return None
