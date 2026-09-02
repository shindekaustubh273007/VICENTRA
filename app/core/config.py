import os
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "IBVAP Video Ingestion & Stream Manager"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./ibvap.db")
    MAX_RETRY_DELAY_SECONDS: int = 60
    DEFAULT_BUFFER_SIZE: int = 10
    API_V1_STR: str = "/api"
    
    class Config:
        env_file = ".env"

settings = Settings()
