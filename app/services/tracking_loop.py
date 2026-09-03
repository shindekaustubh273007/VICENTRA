"""
Phase 3 — Per-camera tracking loop.

Polls ResultStore for new frame detections, runs the tracker,
and stores the updated tracks in TrackedStore.
"""

import threading
import time
from typing import Optional

from app.core.logging import logger
from app.services.tracker import ObjectTracker
from app.services.result_store import result_store
from app.services.tracked_store import tracked_store
from app.core.config import settings

class TrackingLoop:
    def __init__(
        self,
        camera_id: str,
        poll_interval: float = 0.05,
    ):
        self.camera_id = camera_id
        self.tracker = ObjectTracker(camera_id)
        self.poll_interval = poll_interval

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_frame_timestamp: Optional[str] = None
        
        self.status: str = "STOPPED"
        self.frames_processed = 0

    def start(self):
        if self._thread and self._thread.is_alive():
            logger.warning(f"Tracking loop for {self.camera_id} already running.")
            return

        self._stop_event.clear()
        self.status = "RUNNING"
        self._thread = threading.Thread(
            target=self._run,
            name=f"Tracking-{self.camera_id}",
            daemon=True,
        )
        self._thread.start()
        logger.info(f"Tracking loop started for camera {self.camera_id}")

    def stop(self):
        self.status = "STOPPED"
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3.0)
        logger.info(f"Tracking loop stopped for camera {self.camera_id}")

    def _run(self):
        while not self._stop_event.is_set():
            try:
                # Fetch the latest processed frame detections from the inference phase
                latest_detections = result_store.get_latest_detections(self.camera_id)
                
                if not latest_detections:
                    self._stop_event.wait(timeout=self.poll_interval)
                    continue
                    
                current_frame_timestamp = latest_detections[0].frame_timestamp
                
                # Check if we already processed this frame
                if current_frame_timestamp == self._last_frame_timestamp:
                    self._stop_event.wait(timeout=self.poll_interval)
                    continue
                    
                self._last_frame_timestamp = current_frame_timestamp
                
                # Run the tracker with the new detections
                active_tracks = self.tracker.update(latest_detections)
                
                # Store the result for API/downstream consumers
                tracked_store.update_tracks(self.camera_id, active_tracks)
                
                self.frames_processed += 1
                
            except Exception as e:
                logger.error(f"Tracking error for camera {self.camera_id}: {e}")
                
            self._stop_event.wait(timeout=self.poll_interval)

    def get_metrics(self) -> dict:
        return {
            "camera_id": self.camera_id,
            "status": self.status,
            "frames_processed": self.frames_processed,
            "active_tracks": len(self.tracker.tracks),
        }
