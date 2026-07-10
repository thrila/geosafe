from pathlib import Path
from fastapi import  HTTPException, UploadFile
import tempfile
from fastapi import UploadFile
import subprocess

def get_telemetary(name, path):
    # Get the directory where this utils.py file resides
    utils_dir = Path(__file__).parent
    exe_path = utils_dir / "import-logs.exe"

    # Optional: verify it exists
    if not exe_path.exists():
        raise FileNotFoundError(f"Executable not found at {exe_path}")

    result = subprocess.run(
        [str(exe_path), name, path],
        capture_output=True,
        text=True,
    )
    print(result.stdout)


def _validate_upload(upload: UploadFile, kind: str, allowed_extensions: tuple[str, ...]) -> str:
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


def _confidence_to_float(confidence: str) -> float:
    return float(confidence.rstrip("%"))


def _format_confidence(confidence: float) -> str:
    return f"{confidence:.1f}%"


async def _save_upload_to_temp(upload: UploadFile) -> Path:
    suffix = Path(upload.filename or "").suffix.lower()
    contents = await upload.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(contents)
        return Path(temp_file.name)

