import os
import google.auth
from google.auth.exceptions import DefaultCredentialsError
from fastapi import Request, HTTPException
from authlib.integrations.starlette_client import OAuth
from google import genai

from src.core.logger import logger
from src.core.storage import InMemoryStorage, FirestoreStorage

# --- AI Client Initialization ---
try:
    # Initialize Vertex AI client using Application Default Credentials
    # Note: gemini-3.1-flash-lite-preview requires the 'global' location endpoint
    ai_client = genai.Client(vertexai=True, location=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"))
except Exception as e:
    logger.warning(f"Failed to initialize Vertex AI client: {e}")
    ai_client = None

# --- Database Initialization ---
# Select Database based on environment variable (set natively in GCP Cloud Run)
if os.environ.get("ENVIRONMENT") == "production":
    logger.info("Production environment detected, using main Firestore DB")
    db = FirestoreStorage()
else:
    try:
        # Check if Application Default Credentials exist
        google.auth.default()
        
        logger.info("ADC found, using local Firestore DB: run-run-rest-local-db")
        db = FirestoreStorage(database="run-run-rest-local-db")
    except DefaultCredentialsError:
        logger.info("ADC not found, falling back to InMemoryStorage")
        db = InMemoryStorage()
    except Exception as e:
        logger.warning(f"Error checking ADC or initializing local Firestore: {e}. Falling back to InMemoryStorage")
        db = InMemoryStorage()

# --- OAuth Initialization ---
oauth = OAuth()
oauth.register(
    name='zitadel',
    server_metadata_url=os.environ.get('ZITADEL_DISCOVERY_URL'),
    client_id=os.environ.get('ZITADEL_CLIENT_ID'),
    client_secret=os.environ.get('ZITADEL_CLIENT_SECRET'),
    client_kwargs={'scope': 'openid profile email'},
)

# --- FastAPI Dependencies ---
async def get_current_user(request: Request):
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    sub = user.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid session data")

    user_data = await db.get("users", sub)
    if not user_data:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user_data
