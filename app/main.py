from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import setup_logging
from app.database.database import engine, Base
from app.api import cameras, health
from app.services.stream_manager import stream_manager
import os

# Initialize database
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup
    setup_logging()
    
    # Pre-start enabled cameras on startup
    from app.database.database import SessionLocal
    from app.database import models
    db = SessionLocal()
    try:
        active_cams = db.query(models.Camera).filter(models.Camera.enabled == True).all()
        for cam in active_cams:
            stream_manager.start_stream(
                camera_id=cam.camera_id,
                source_type=cam.source_type,
                source_url=cam.source_url,
                target_fps=cam.target_fps,
                buffer_size=cam.buffer_size
            )
    finally:
        db.close()
        
    yield
    
    # Teardown
    stream_manager.shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(cameras.router, prefix=f"{settings.API_V1_STR}/cameras", tags=["Cameras"])
app.include_router(health.router, prefix=f"{settings.API_V1_STR}/health", tags=["Health"])

# Static Dashboard (ensure dir exists)
os.makedirs("static", exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
