from pydantic_settings import BaseSettings
from typing import Optional,ClassVar
from pathlib import  WindowsPath

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "GeoSafe"
    VERSION: str = "0.1.0"
    ENV: str = "development"  # development, staging, production
    
    #Media Formats
    IMAGE_EXTENSIONS: tuple[str, ...] = (".jpg", ".jpeg", ".png", ".webp")
    VIDEO_EXTENSIONS: tuple[str, ...] = (".mp4", ".avi", ".mov", ".mkv")

    # CAPTURE Settings 
    IMAGE_SIZE:int = 224
    INTERVAL_SECONDS:float = 2.0
    BLUR_THRESHOLD:float = 100.0
    # TEMP dir
    #NOTE: Check default video source and consider changing it
    DEFAULT_OUTPUT_DIR:WindowsPath= WindowsPath("captured_frames")
    DEFAULT_VIDEO_SOURCE:WindowsPath= WindowsPath("video.mp4")

    #API INFO
    API_VERSION: str = "/api/v1"
    TITLE: str= "Maize Disease Detection API"

    #MODELS
    DEFAULT_MODEL: ClassVar[WindowsPath] = WindowsPath("models/model.pt")
    LEGACY_MODEL: ClassVar[WindowsPath] = WindowsPath("models/best_model.pt")


    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost/db"
    DB_POOL_SIZE: int = 10
    
    # Security
    SECRET_KEY: str= ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # External APIs
    REDIS_URL: Optional[str] = None
    
    model_config = {
            "env_file": ".env",
            "env_file_encoding": "utf-8",
            "case_sensitive": True
        }
# Create a single settings object to import everywhere
settings = Settings()
