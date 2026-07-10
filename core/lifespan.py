# core/lifespan.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.concurrency import run_in_threadpool
from controllers.predict import load_model
from core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    model, class_names = await run_in_threadpool(load_model, settings.DEFAULT_MODEL)
    app.state.model = model
    app.state.class_names = class_names
    yield
