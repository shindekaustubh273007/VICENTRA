"""
Phase 2 — Thread-safe bounded result store for AI detections.

Mirrors the FrameBuffer pattern: one deque per camera, automatic eviction.
"""

import threading
import collections
from typing import List, Dict, Optional

from app.services.detector import Detection
from app.core.config import settings


class ResultStore:
    """
    Stores recent Detection objects per camera_id in bounded deques.
    Thread-safe for concurrent reads/writes from InferenceLoop threads.
    """

    def __init__(self, max_per_camera: int = None):
        self.max_per_camera = max_per_camera or settings.AI_MAX_RESULTS_PER_CAMERA
        self._store: Dict[str, collections.deque] = {}
        self._lock = threading.Lock()

    # ── Writes ───────────────────────────────────────────────────────

    def add_detections(self, camera_id: str, detections: List[Detection]):
        """Append detections. Oldest entries auto-evicted when the deque is full."""
        if not detections:
            return
        with self._lock:
            if camera_id not in self._store:
                self._store[camera_id] = collections.deque(
                    maxlen=self.max_per_camera
                )
            for d in detections:
                self._store[camera_id].append(d)

    # ── Reads ────────────────────────────────────────────────────────

    def get_detections(
        self, camera_id: str, limit: int = 50
    ) -> List[Detection]:
        """Return the most recent *limit* detections for a camera."""
        with self._lock:
            if camera_id not in self._store:
                return []
            items = list(self._store[camera_id])
            return items[-limit:]

    def get_latest_detections(self, camera_id: str) -> List[Detection]:
        """Return all detections from the most recent processed frame."""
        with self._lock:
            if camera_id not in self._store or not self._store[camera_id]:
                return []
            latest_ts = self._store[camera_id][-1].frame_timestamp
            return [
                d
                for d in self._store[camera_id]
                if d.frame_timestamp == latest_ts
            ]

    # ── Maintenance ──────────────────────────────────────────────────

    def clear(self, camera_id: str = None):
        """Clear detections for one camera, or all cameras if camera_id is None."""
        with self._lock:
            if camera_id:
                self._store.pop(camera_id, None)
            else:
                self._store.clear()

    def camera_ids(self) -> List[str]:
        """Return list of camera_ids that have stored detections."""
        with self._lock:
            return list(self._store.keys())


# Module-level singleton
result_store = ResultStore()
