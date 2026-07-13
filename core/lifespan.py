from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from starlette.concurrency import run_in_threadpool

from controllers.predict import load_model
from core.config import settings


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        model, class_names = await run_in_threadpool(
            load_model, settings.DEFAULT_MODEL
        )
        app.state.model = model
        app.state.class_names = class_names
    except FileNotFoundError:
        logger.exception(
            "Model file not found at %s. Set DEFAULT_MODEL in config.",
            settings.DEFAULT_MODEL,
        )
        raise
    except Exception:
        logger.exception("Failed to load model during startup.")
        raise
    yield
