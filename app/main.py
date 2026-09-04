import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import setup_logging
from app.database.database import engine, Base
from app.api import cameras, health
from app.api.detections import ai_router
from app.api.tracking import router as tracking_router
from app.api.zones import camera_zone_router, zone_router
from app.api.events import router as events_router
from app.api.ws import router as ws_router
from app.services.stream_manager import stream_manager
from app.services.inference_manager import inference_manager
from app.services.tracking_manager import tracking_manager
from app.services.zone_manager import zone_manager
from app.services.event_dispatcher import event_dispatcher
from app.services.ws_manager import ws_manager
from app.services.event_store import event_store
from app.core.paths import get_resource_path

# Initialize database
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup
    setup_logging()
    
    # Phase 5: Setup Event Dispatcher and WebSocket broadcasting
    loop = asyncio.get_running_loop()
    event_dispatcher.set_loop(loop)
    event_dispatcher.subscribe(ws_manager.broadcast)
    event_store.on_event = event_dispatcher.publish

    zone_manager.load_zones_from_db()
    
    # Pre-start enabled cameras on startup
    from app.database.database import SessionLocal
    from app.database import models
    db = SessionLocal()
    try:
        active_cams = db.query(models.Camera).filter(models.Camera.enabled == True).all()
        for cam in active_cams:
            started = stream_manager.start_stream(
                camera_id=cam.camera_id,
                source_type=cam.source_type,
                source_url=cam.source_url,
                target_fps=cam.target_fps,
                buffer_size=cam.buffer_size
            )
            if started:
                inference_manager.start_inference(camera_id=cam.camera_id)
                tracking_manager.start_tracking(camera_id=cam.camera_id)
                zone_manager.start_zone_evaluation(camera_id=cam.camera_id)
    finally:
        db.close()
        
    yield
    
    # Teardown
    await ws_manager.disconnect_all()
    event_dispatcher.clear()
    event_store.on_event = None

    zone_manager.shutdown()
    tracking_manager.shutdown()
    inference_manager.shutdown()
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
app.include_router(camera_zone_router, prefix=f"{settings.API_V1_STR}/cameras", tags=["Zones"])
app.include_router(zone_router, prefix=f"{settings.API_V1_STR}/zones", tags=["Zones"])
app.include_router(events_router, prefix=f"{settings.API_V1_STR}/events", tags=["Events"])
app.include_router(ws_router, prefix=f"{settings.API_V1_STR}/events", tags=["Events WebSocket"])
app.include_router(ai_router, prefix=f"{settings.API_V1_STR}/ai", tags=["AI Engine"])
app.include_router(tracking_router, prefix=f"{settings.API_V1_STR}/tracking", tags=["Tracking"])
app.include_router(health.router, prefix=f"{settings.API_V1_STR}/health", tags=["Health"])

# Static Dashboard
static_dir = get_resource_path("static")
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
