import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/ping")
def ping():
    logger.info("Ping endpoint")
    return {"status": "ok", "message": "pong"}

@router.get("/health")
def health():
    logger.info("Health endpoint")
    return {"status": "ok"}

