from fastapi import APIRouter 
from core.config import settings  # your settings

health_router = APIRouter()



@health_router.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "version": settings.VERSION,
        "environment": settings.ENV
    }
