import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.core.paths import get_database_url

class Settings(BaseSettings):
    PROJECT_NAME: str = "IBVAP Video Ingestion & Stream Manager"
    DATABASE_URL: str = Field(default_factory=get_database_url)
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
    
    # --- Phase 3: Object Tracking ---
    TRACKING_ENABLED: bool = True
    TRACKING_MAX_MISSED_FRAMES: int = 5
    TRACKING_MAX_HISTORY: int = 50
    TRACKING_ASSOCIATION_THRESHOLD: float = 50.0  # Pixel distance threshold
    
    # --- Phase 4: Virtual Fences & Zones ---
    ZONES_ENABLED: bool = True
    ZONE_MAX_EVENTS_PER_CAMERA: int = 500
    ZONE_EVALUATION_FPS: float = 5.0

    # --- Phase 5: Real-Time Alerts & Events ---
    WS_ENABLED: bool = True
    WS_MAX_CLIENTS: int = 50
    DASHBOARD_MAX_ALERTS: int = 50

    # --- Phase 6: Packaging & Deployment ---
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8000
    AUTO_OPEN_BROWSER: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
