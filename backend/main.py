from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import settings
from core.lifespan import lifespan
from routes.docs import docs_route
from routes.flights import flights_router
from routes.health import health_router
from routes.images import image_router
from routes.upload import upload_router
from routes.videos import video_router
from utils.banner import banner


app = FastAPI(
    title=settings.TITLE,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.API_VERSION)
app.include_router(image_router, prefix=settings.API_VERSION)
app.include_router(video_router, prefix=settings.API_VERSION)
app.include_router(upload_router, prefix=settings.API_VERSION)
app.include_router(flights_router, prefix=settings.API_VERSION)
app.include_router(docs_route)

output_images = Path("output") / "images"
output_images.mkdir(parents=True, exist_ok=True)
app.mount("/api/v1/images", StaticFiles(directory=str(output_images)), name="images")


if __name__ == "__main__":
    import uvicorn

    banner()
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.RELOAD)
