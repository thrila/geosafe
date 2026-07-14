import asyncio
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from starlette.concurrency import run_in_threadpool

from core.config import settings
from pipeline.config import Config
from pipeline.inference import Pipeline

logger = logging.getLogger(__name__)

_TTL_CLEANUP_INTERVAL = 3600  # seconds between cleanup sweeps


async def _cleanup_old_files():
    """Delete files in output/images/ and output/metadata/ older than TTL."""
    ttl_seconds = settings.TEMP_FILE_TTL_HOURS * 3600
    now = time.time()
    dirs = [Path("output") / "images", Path("output") / "metadata"]
    while True:
        await asyncio.sleep(_TTL_CLEANUP_INTERVAL)
        for d in dirs:
            if not d.exists():
                continue
            for p in d.iterdir():
                if p.is_file() and (now - p.stat().st_mtime) > ttl_seconds:
                    try:
                        p.unlink(missing_ok=True)
                        logger.debug("Cleaned up expired temp file: %s", p)
                    except OSError:
                        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    ready = asyncio.Event()
    app.state.pipeline_ready = ready

    async def _load():
        try:
            config = Config()
            pipeline = await run_in_threadpool(Pipeline, config)
            app.state.pipeline = pipeline
            logger.info("Pipeline loaded")
        except Exception:
            logger.exception("Pipeline loading failed — requests will fail until models are loaded")
        finally:
            ready.set()

    load_task = asyncio.create_task(_load())
    cleanup_task = asyncio.create_task(_cleanup_old_files())
    yield

    cleanup_task.cancel()
    load_task.cancel()
    for t in (load_task, cleanup_task):
        try:
            await t
        except asyncio.CancelledError:
            pass
