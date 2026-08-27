import asyncio
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from starlette.concurrency import run_in_threadpool

from core.config import settings
from pipeline.config import Config
from pipeline.inference import Pipeline
from services.flights import FlightService
from services.log_importer import DJIFlightLogImporter, LogImportError
from services.upload_jobs import UploadJobService

logger = logging.getLogger(__name__)

_TTL_CLEANUP_INTERVAL = 3600  # seconds between cleanup sweeps


async def _cleanup_old_files():
    """Remove complete, expired flight artifact directories."""
    ttl_seconds = settings.TEMP_FILE_TTL_HOURS * 3600
    while True:
        await asyncio.sleep(_TTL_CLEANUP_INTERVAL)
        now = time.time()
        output_dir = settings.OUTPUT_DIR
        if not output_dir.exists():
            continue
        for artifact_dir in output_dir.iterdir():
            if not artifact_dir.is_dir():
                continue
            try:
                if now - artifact_dir.stat().st_mtime > ttl_seconds:
                    for path in artifact_dir.rglob("*"):
                        if path.is_file():
                            path.unlink(missing_ok=True)
                    for path in sorted(artifact_dir.rglob("*"), reverse=True):
                        if path.is_dir():
                            path.rmdir()
                    artifact_dir.rmdir()
                    logger.debug("Cleaned up expired flight artifacts: %s", artifact_dir)
            except OSError:
                logger.warning("Could not clean up expired artifacts: %s", artifact_dir)


async def _process_upload_jobs(app: FastAPI, jobs: UploadJobService) -> None:
    """Claim durable jobs one at a time; SQLite makes claims safe across workers."""
    importer = DJIFlightLogImporter()
    flights = FlightService()
    while True:
        try:
            job = await run_in_threadpool(jobs.claim_next)
        except Exception:
            # A transient SQLite failure must not make the API's lifespan fail.
            # Keeping the job queued also lets a later worker retry it safely.
            logger.exception("Could not claim the next upload job")
            await asyncio.sleep(1)
            continue
        if job is None:
            await asyncio.sleep(0.5)
            continue

        try:
            await app.state.pipeline_ready.wait()
            pipeline = app.state.pipeline
            flight_id = await run_in_threadpool(
                importer.import_log, job["name"], Path(job["logPath"]).resolve()
            )
            await run_in_threadpool(jobs.set_status, job["id"], "processing")
            artifact_id = uuid4().hex
            artifact_dir = settings.OUTPUT_DIR / artifact_id
            video_result = await run_in_threadpool(
                pipeline.process_video,
                Path(job["videoPath"]).resolve(),
                artifact_dir,
                f"/api/v1/images/{artifact_id}",
            )
            response = await flights.build_upload_response(
                video_result, job["name"], flight_id, artifact_id
            )
            await run_in_threadpool(jobs.complete, job["id"], response)
        except LogImportError as exc:
            await run_in_threadpool(jobs.fail, job["id"], str(exc))
        except (OSError, IOError, ValueError) as exc:
            await run_in_threadpool(jobs.fail, job["id"], f"Could not process video: {exc}")
        except Exception:
            logger.exception("Upload job %s failed", job["id"])
            await run_in_threadpool(jobs.fail, job["id"], "An internal error occurred.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    ready = asyncio.Event()
    app.state.pipeline_ready = ready
    upload_jobs = UploadJobService()
    await run_in_threadpool(upload_jobs.requeue_interrupted)
    app.state.upload_jobs = upload_jobs

    async def _load():
        try:
            config = Config(fps=settings.VIDEO_SAMPLE_FPS)
            pipeline = await run_in_threadpool(Pipeline, config)
            app.state.pipeline = pipeline
            logger.info("Pipeline loaded")
        except Exception:
            logger.exception("Pipeline loading failed — requests will fail until models are loaded")
        finally:
            ready.set()

    load_task = asyncio.create_task(_load())
    cleanup_task = asyncio.create_task(_cleanup_old_files())
    upload_worker_task = asyncio.create_task(_process_upload_jobs(app, upload_jobs))
    yield

    cleanup_task.cancel()
    load_task.cancel()
    upload_worker_task.cancel()
    for t in (load_task, cleanup_task, upload_worker_task):
        try:
            await t
        except asyncio.CancelledError:
            pass
