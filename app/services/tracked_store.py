"""
Phase 3 — Thread-safe store for tracked objects.
Mirrors ResultStore pattern.
"""
import threading
from typing import List, Dict

from app.services.tracker import TrackedObject

class TrackedStore:
    def __init__(self):
        # We store the *latest* active tracks for each camera.
        self._store: Dict[str, List[TrackedObject]] = {}
        self._lock = threading.Lock()

    def update_tracks(self, camera_id: str, tracks: List[TrackedObject]):
        """Overwrite the current active tracks for the camera."""
        with self._lock:
            self._store[camera_id] = list(tracks)

    def get_tracks(self, camera_id: str) -> List[TrackedObject]:
        """Return the current active tracks for a camera."""
        with self._lock:
            if camera_id not in self._store:
                return []
            return list(self._store[camera_id])

    def clear(self, camera_id: str = None):
        """Clear tracks for one camera, or all cameras if camera_id is None."""
        with self._lock:
            if camera_id:
                self._store.pop(camera_id, None)
            else:
                self._store.clear()

# Module-level singleton
tracked_store = TrackedStore()
