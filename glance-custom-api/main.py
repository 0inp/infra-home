import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from github import Auth, Github
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build

from routes import github, health, youtube

logging.basicConfig(
    level=logging.DEBUG,  # Change to INFO if you want less verbosity
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

YOUTUBE_SCOPES: list[str] = ["https://www.googleapis.com/auth/youtube.readonly"]
YOUTUBE_TOKEN_FILE: str = "credentials/token.json"
GITHUB_TOKEN_FILE: str = "/run/secrets/github-token"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up...")
    logger.info("Creating YouTube client...")

    if not os.path.exists(YOUTUBE_TOKEN_FILE):
        logger.error("Token file not found at %s", YOUTUBE_TOKEN_FILE)
        raise RuntimeError(
            "Token file not found. Run generate_token.py locally to generate it."
        )

    creds = Credentials.from_authorized_user_file(YOUTUBE_TOKEN_FILE, YOUTUBE_SCOPES)

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                logger.info("Refreshing expired YouTube token...")
                creds.refresh(Request())
                # Save the refreshed credentials
                with open(YOUTUBE_TOKEN_FILE, "w") as token:
                    token.write(creds.to_json())
                logger.info("YouTube token refreshed and saved.")
            except RefreshError as e:
                logger.error("Error refreshing token: %s", e)
                raise RuntimeError(
                    "Failed to refresh token. Please run generate_token.py again."
                )
        else:
            raise RuntimeError(
                "Invalid credentials. Please run generate_token.py again."
            )

    youtube_client: Resource = build("youtube", "v3", credentials=creds)
    app.state.youtube_client = youtube_client
    logger.info("YouTube client created.")

    logger.info("Creating Github client...")
    if not os.path.exists(GITHUB_TOKEN_FILE):
        logger.error("GitHub token file not found at %s", GITHUB_TOKEN_FILE)
        raise RuntimeError("GitHub token not configured.")

    with open(GITHUB_TOKEN_FILE, "r") as f:
        token = f.read().strip()

    auth = Auth.Token(token=token)
    github_client = Github(auth=auth)
    app.state.github_client = github_client

    logger.info("GitHub client created with token")
    yield

    # Shutdown
    logger.info("Shutting down.")


app = FastAPI(title="Glance Custom API", lifespan=lifespan)

# Register routes
app.include_router(health.router)
app.include_router(youtube.router)
app.include_router(github.router)
