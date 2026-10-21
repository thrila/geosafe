from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from core.config import settings

health_router = APIRouter()


@health_router.get("/health")
async def health(request: Request):
    ready = getattr(request.app.state, "pipeline_ready", None)
    status = getattr(request.app.state, "pipeline_status", "starting")
    if ready is None or not ready.is_set() or status == "starting":
        return JSONResponse(
            status_code=503,
            content={"status": "starting", "version": settings.VERSION, "environment": settings.ENV},
        )
    if status != "ready" or not hasattr(request.app.state, "pipeline"):
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "detail": "The analysis pipeline failed to initialize. Check the backend logs.",
                "version": settings.VERSION,
                "environment": settings.ENV,
            },
        )
    return {
        "status": "ok",
        "version": settings.VERSION,
        "environment": settings.ENV
    }
