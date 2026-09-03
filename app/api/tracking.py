from fastapi import APIRouter, HTTPException, Depends
from typing import Any

from app.models.schemas import TrackingResponse
from app.services.tracked_store import tracked_store
from app.services.tracking_manager import tracking_manager

router = APIRouter()

@router.get("/{camera_id}", response_model=TrackingResponse)
def get_tracked_objects(camera_id: str) -> Any:
    """
    Get the currently active tracked objects for a specific camera.
    """
    tracks = tracked_store.get_tracks(camera_id)
    return {
        "camera_id": camera_id,
        "count": len(tracks),
        "tracks": [t.to_dict() for t in tracks]
    }

@router.get("/status/all")
def get_tracking_status() -> Any:
    """
    Get the status of all tracking loops.
    """
    return tracking_manager.get_all_status()
