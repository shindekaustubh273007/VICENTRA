"""
Phase 3 — TrackingManager: singleton orchestrator for tracking loops.
"""

from typing import Dict, Optional
from app.services.tracking_loop import TrackingLoop
from app.core.config import settings
from app.core.logging import logger
from app.services.tracked_store import tracked_store

class TrackingManager:
    """
    Manages camera_id → TrackingLoop mappings.
    """
    def __init__(self):
        self._loops: Dict[str, TrackingLoop] = {}
        self._enabled: bool = settings.TRACKING_ENABLED

    def start_tracking(self, camera_id: str) -> bool:
        if not self._enabled:
            logger.info(f"Tracking disabled — skipping camera {camera_id}")
            return False

        existing = self._loops.get(camera_id)
        if existing and existing.status == "RUNNING":
            return False

        loop = TrackingLoop(camera_id=camera_id)
        self._loops[camera_id] = loop
        loop.start()
        return True

    def stop_tracking(self, camera_id: str) -> bool:
        loop = self._loops.get(camera_id)
        if not loop or loop.status == "STOPPED":
            return False
        loop.stop()
        tracked_store.clear(camera_id)
        return True

    def remove_tracking(self, camera_id: str):
        self.stop_tracking(camera_id)
        self._loops.pop(camera_id, None)

    def get_status(self, camera_id: str) -> Optional[dict]:
        loop = self._loops.get(camera_id)
        if not loop:
            return None
        return loop.get_metrics()

    def get_all_status(self) -> dict:
        per_camera = [loop.get_metrics() for loop in self._loops.values()]
        return {
            "tracking_enabled": self._enabled,
            "cameras": per_camera,
        }

    def shutdown(self):
        logger.info("Shutting down TrackingManager…")
        for loop in self._loops.values():
            loop.stop()
        self._loops.clear()
        tracked_store.clear()


# Module-level singleton
tracking_manager = TrackingManager()
