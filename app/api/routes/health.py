from datetime import datetime

from fastapi import APIRouter, Depends

from app.api.dependencies import get_settings_dependency
from app.core.config import Settings

router = APIRouter()


@router.get("/live", summary="Liveness probe")
def liveness(settings: Settings = Depends(get_settings_dependency)):
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/ready", summary="Readiness probe")
def readiness(settings: Settings = Depends(get_settings_dependency)):
    return {
        "status": "ready",
        "version": settings.VERSION,
        "gemini_model": settings.GEMINI_MODEL,
    }
