from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from core.config import settings  # your settings

health_router = APIRouter()



@health_router.get("/health")
async def health(request: Request):
    ready = getattr(request.app.state, "pipeline_ready", None)
    if ready is None or not ready.is_set() or not hasattr(request.app.state, "pipeline"):
        return JSONResponse(
            status_code=503,
            content={"status": "starting", "version": settings.VERSION, "environment": settings.ENV},
        )
    return {
        "status": "ok",
        "version": settings.VERSION,
        "environment": settings.ENV
    }
