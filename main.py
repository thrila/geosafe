from __future__ import annotations
from fastapi.middleware.cors import CORSMiddleware
from  routes.health import health_router
from routes.images import image_router
from routes.videos import video_router
from routes.upload import upload_router
from routes.docs import docs_route
from core.config import settings
from core.lifespan import lifespan
from utils.banner import banner

from fastapi import FastAPI



app = FastAPI(
    title=settings.TITLE,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.API_VERSION)
app.include_router(image_router, prefix=settings.API_VERSION)
app.include_router(video_router, prefix=settings.API_VERSION)
app.include_router(upload_router, prefix=settings.API_VERSION)
app.include_router(docs_route)


if __name__ == "__main__":
    import uvicorn
    banner()

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
