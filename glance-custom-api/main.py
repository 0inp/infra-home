import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build

from routes import health, youtube

logging.basicConfig(
    level=logging.DEBUG,  # Change to INFO if you want less verbosity
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

SCOPES: list[str] = ["https://www.googleapis.com/auth/youtube.readonly"]
TOKEN_FILE: str = "credentials/token.json"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up and creating YouTube client...")
    if not os.path.exists(TOKEN_FILE):
        logger.error("Token file not found at %s", TOKEN_FILE)
        raise RuntimeError(
            "Token file not found. Run OAuth flow locally to generate it."
        )

    creds: Credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    youtube_client: Resource = build("youtube", "v3", credentials=creds)
    app.state.youtube_client = youtube_client
    logger.info("YouTube client created.")
    yield
    # Shutdown
    logger.info("Shutting down.")


app = FastAPI(title="Glance Custom API", lifespan=lifespan)

# Register routes
app.include_router(health.router)
app.include_router(youtube.router)
