import logging
import tempfile
from pathlib import Path

from fastapi import HTTPException, UploadFile

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


def confidence_to_float(confidence: str) -> float:
    return float(confidence.rstrip("%"))


def format_confidence(confidence: float) -> str:
    return f"{confidence:.1f}%"


async def save_upload_to_temp(upload: UploadFile) -> Path:
    suffix = Path(upload.filename or "").suffix.lower()
    contents = await upload.read()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(contents)
        return Path(temp_file.name)
