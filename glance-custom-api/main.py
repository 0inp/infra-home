import logging
from fastapi import FastAPI
from routes import health, youtube


logging.basicConfig(
    level=logging.DEBUG,  # Change to INFO if you want less verbosity
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Glance Custom API")

# Register routes
app.include_router(health.router)
app.include_router(youtube.router)
