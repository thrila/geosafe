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
from services.flight_processing import FlightProcessingService
from services.log_importer import DJIFlightLogImporter, LogImportError
from services.telemetry import SqliteFlightRepository
from services.upload_jobs import SqliteUploadJobRepository, UploadJobRepository
from services.upload_storage import LocalUploadStorage

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


async def _keep_claim_alive(
    jobs: UploadJobRepository, job_id: str, worker_id: str
) -> None:
    """Renew a long-running job lease so another process cannot reclaim it."""
    interval = max(1, settings.UPLOAD_JOB_LEASE_SECONDS // 3)
    while True:
        await asyncio.sleep(interval)
        try:
            renewed = await run_in_threadpool(
                jobs.renew_claim,
                job_id,
                worker_id,
                settings.UPLOAD_JOB_LEASE_SECONDS,
            )
        except Exception:
            logger.exception("Could not renew upload-job lease for %s", job_id)
            return
        if not renewed:
            logger.error("Lost upload-job lease for %s", job_id)
            return


async def _process_upload_jobs(
    app: FastAPI, jobs: UploadJobRepository, worker_id: str
) -> None:
    """Lease durable jobs one at a time and retain ownership while they run."""
    flight_processing: FlightProcessingService = app.state.flight_processing
    while True:
        try:
            job = await run_in_threadpool(
                jobs.claim_next, worker_id, settings.UPLOAD_JOB_LEASE_SECONDS
            )
        except Exception:
            # A transient SQLite failure must not make the API's lifespan fail.
            # Keeping the job queued also lets a later worker retry it safely.
            logger.exception("Could not claim the next upload job")
            await asyncio.sleep(1)
            continue
        if job is None:
            await asyncio.sleep(0.5)
            continue

        heartbeat_task = asyncio.create_task(
            _keep_claim_alive(jobs, job["id"], worker_id)
        )
        try:
            await app.state.pipeline_ready.wait()
            pipeline = app.state.pipeline
            flight_id = job["flightId"]
            if flight_id is None:
                flight_id = await flight_processing.import_log(job["name"], Path(job["logPath"]))
                recorded = await run_in_threadpool(
                    jobs.record_flight_id,
                    job["id"],
                    worker_id,
                    flight_id,
                    settings.UPLOAD_JOB_LEASE_SECONDS,
                )
                if not recorded:
                    raise RuntimeError("Upload job lease was lost after log import.")

            artifact_id = job["artifactId"] or uuid4().hex
            processing_started = await run_in_threadpool(
                jobs.begin_processing,
                job["id"],
                worker_id,
                artifact_id,
                settings.UPLOAD_JOB_LEASE_SECONDS,
            )
            if not processing_started:
                raise RuntimeError("Upload job lease was lost before video processing.")
            artifact_dir = settings.OUTPUT_DIR / artifact_id
            response = await flight_processing.analyze_video(
                pipeline,
                job["name"],
                Path(job["videoPath"]),
                flight_id,
                artifact_id,
                artifact_dir,
            )
            completed = await run_in_threadpool(
                jobs.complete, job["id"], worker_id, response
            )
            if not completed:
                logger.error("Upload job %s completed after its lease was lost", job["id"])
        except LogImportError as exc:
            await run_in_threadpool(jobs.fail, job["id"], worker_id, str(exc))
        except (OSError, IOError, ValueError) as exc:
            await run_in_threadpool(
                jobs.fail, job["id"], worker_id, f"Could not process video: {exc}"
            )
        except Exception:
            logger.exception("Upload job %s failed", job["id"])
            await run_in_threadpool(
                jobs.fail, job["id"], worker_id, "An internal error occurred."
            )
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    ready = asyncio.Event()
    app.state.pipeline_ready = ready
    upload_jobs: UploadJobRepository = SqliteUploadJobRepository()
    await run_in_threadpool(upload_jobs.requeue_expired)
    app.state.upload_jobs = upload_jobs
    app.state.upload_storage = LocalUploadStorage()
    app.state.log_importer = DJIFlightLogImporter()
    app.state.flight_service = FlightService(SqliteFlightRepository())
    app.state.flight_processing = FlightProcessingService(
        app.state.log_importer, app.state.flight_service
    )
    upload_worker_id = uuid4().hex

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
    upload_worker_task = asyncio.create_task(
        _process_upload_jobs(app, upload_jobs, upload_worker_id)
    )
    yield

    cleanup_task.cancel()
    load_task.cancel()
    upload_worker_task.cancel()
    for t in (load_task, cleanup_task, upload_worker_task):
        try:
            await t
        except asyncio.CancelledError:
            pass
