import logging
import tempfile
from pathlib import Path

from fastapi import HTTPException, Request, UploadFile

from core.config import settings

logger = logging.getLogger(__name__)


def validate_upload(upload: UploadFile, kind: str, allowed_extensions: tuple[str, ...]) -> str:
    filename = upload.filename or ""
    suffix = Path(filename).suffix.lower()
    content_type = (upload.content_type or "").lower()

    if not content_type.startswith(f"{kind}/") or suffix not in allowed_extensions:
        allowed = ", ".join(allowed_extensions)
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid {kind} upload. MIME type must start with '{kind}/' "
                f"and extension must be one of: {allowed}."
            ),
        )

    return suffix


def require_ready_pipeline(request: Request) -> None:
    """Return a service-unavailable response until inference can run."""
    status = getattr(request.app.state, "pipeline_status", "starting")
    if status == "ready":
        return
    if status == "starting":
        detail = "The analysis pipeline is still starting. Try again shortly."
    else:
        detail = "The analysis pipeline is unavailable. Check the backend logs."
    raise HTTPException(status_code=503, detail=detail)


def confidence_to_float(confidence: str) -> float:
    return float(confidence.rstrip("%"))


def format_confidence(confidence: float) -> str:
    return f"{confidence:.1f}%"


async def save_upload_to_temp(upload: UploadFile, max_bytes: int = settings.MAX_UPLOAD_BYTES) -> Path:
    suffix = Path(upload.filename or "").suffix.lower()
    temp_path: Path | None = None
    total = 0
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = Path(temp_file.name)
            while chunk := await upload.read(settings.UPLOAD_CHUNK_BYTES):
                total += len(chunk)
                if total > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Upload exceeds the {max_bytes // (1024 * 1024)} MiB limit.",
                    )
                temp_file.write(chunk)
        if total == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        return temp_path
    except Exception:
        if temp_path:
            temp_path.unlink(missing_ok=True)
        raise


async def save_upload_to_path(
    upload: UploadFile, destination: Path, max_bytes: int = settings.MAX_UPLOAD_BYTES
) -> Path:
    """Stream an upload to its durable job-owned destination."""
    total = 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("wb") as output:
            while chunk := await upload.read(settings.UPLOAD_CHUNK_BYTES):
                total += len(chunk)
                if total > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Upload exceeds the {max_bytes // (1024 * 1024)} MiB limit.",
                    )
                output.write(chunk)
        if total == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        return destination
    except Exception:
        destination.unlink(missing_ok=True)
        raise
