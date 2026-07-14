from pathlib import Path
from typing import ClassVar, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "GeoSafe"
    VERSION: str = "0.1.0"
    ENV: str = "development"

    IMAGE_EXTENSIONS: tuple[str, ...] = (".jpg", ".jpeg", ".png", ".webp")
    VIDEO_EXTENSIONS: tuple[str, ...] = (".mp4", ".avi", ".mov", ".mkv")

    IMAGE_SIZE: int = 224
    INTERVAL_SECONDS: float = 2.0
    BLUR_THRESHOLD: float = 100.0

    DEFAULT_OUTPUT_DIR: Path = Path("captured_frames")
    DEFAULT_VIDEO_SOURCE: Path = Path("video.mp4")

    API_VERSION: str = "/api/v1"
    TITLE: str = "Maize Disease Detection API"

    DEFAULT_MODEL: ClassVar[Path] = Path("models/model.pt")
    LEGACY_MODEL: ClassVar[Path] = Path("models/best_model.pt")

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost/db"
    DB_POOL_SIZE: int = 10

    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    REDIS_URL: Optional[str] = None

    TEMP_FILE_TTL_HOURS: int = 48

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()
