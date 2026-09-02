import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "IBVAP Video Ingestion & Stream Manager"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./ibvap.db")
    MAX_RETRY_DELAY_SECONDS: int = 60
    DEFAULT_BUFFER_SIZE: int = 10
    API_V1_STR: str = "/api"

    # --- Phase 2: AI Inference ---
    AI_ENABLED: bool = True
    AI_MODEL: str = "yolov8n.pt"
    AI_DEVICE: str = "auto"            # "auto", "cuda", "cpu"
    AI_CONFIDENCE_THRESHOLD: float = 0.4
    AI_IOU_THRESHOLD: float = 0.45
    AI_INFERENCE_FPS: float = 2.0
    AI_MAX_RESULTS_PER_CAMERA: int = 100
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
