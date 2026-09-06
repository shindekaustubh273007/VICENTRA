"""
Phase 4 — Thread-safe bounded event store for Zone & Intrusion events.

Mirrors ResultStore and TrackedStore patterns.
"""

import threading
import collections
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Callable
from datetime import datetime

from app.core.config import settings


@dataclass
class ZoneEvent:
    event_id: str
    event_type: str                            # "ENTER", "EXIT", "INTRUSION"
    camera_id: str
    zone_id: str
    zone_name: str
    track_id: str
    object_class: str
    category: str
    timestamp: datetime
    position: Tuple[float, float]               # (x, y) coordinates at event time

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "camera_id": self.camera_id,
            "zone_id": self.zone_id,
            "zone_name": self.zone_name,
            "track_id": self.track_id,
            "object_class": self.object_class,
            "category": self.category,
            "timestamp": self.timestamp.isoformat(),
            "position": {"x": round(self.position[0], 2), "y": round(self.position[1], 2)},
        }


class EventStore:
    """
    Stores recent ZoneEvent objects per camera_id and globally in bounded deques.
    Thread-safe for concurrent writes from ZoneEvaluationLoops and reads from API.
    """

    def __init__(self, max_per_camera: int = None):
        self.max_per_camera = max_per_camera or settings.ZONE_MAX_EVENTS_PER_CAMERA
        self._store: Dict[str, collections.deque] = {}
        self._global_store = collections.deque(maxlen=self.max_per_camera * 2)
        self._lock = threading.Lock()
        self.on_event: Optional[Callable] = None

    def add_event(self, event: ZoneEvent):
        with self._lock:
            if event.camera_id not in self._store:
                self._store[event.camera_id] = collections.deque(maxlen=self.max_per_camera)
            self._store[event.camera_id].append(event)
            self._global_store.append(event)

        if self.on_event:
            try:
                self.on_event(event)
            except Exception:
                pass

    def get_events(
        self,
        camera_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[ZoneEvent]:
        with self._lock:
            if camera_id:
                source = list(self._store.get(camera_id, []))
            else:
                source = list(self._global_store)

            filtered = source
            if zone_id:
                filtered = [e for e in filtered if e.zone_id == zone_id]
            if event_type:
                filtered = [e for e in filtered if e.event_type == event_type.upper()]

            return filtered[-limit:]

    def clear(self, camera_id: Optional[str] = None, zone_id: Optional[str] = None):
        with self._lock:
            if zone_id and camera_id:
                if camera_id in self._store:
                    self._store[camera_id] = collections.deque(
                        [e for e in self._store[camera_id] if e.zone_id != zone_id],
                        maxlen=self.max_per_camera,
                    )
                self._global_store = collections.deque(
                    [e for e in self._global_store if not (e.camera_id == camera_id and e.zone_id == zone_id)],
                    maxlen=self._global_store.maxlen,
                )
            elif zone_id:
                for cam_id in list(self._store.keys()):
                    self._store[cam_id] = collections.deque(
                        [e for e in self._store[cam_id] if e.zone_id != zone_id],
                        maxlen=self.max_per_camera,
                    )
                self._global_store = collections.deque(
                    [e for e in self._global_store if e.zone_id != zone_id],
                    maxlen=self._global_store.maxlen,
                )
            elif camera_id:
                self._store.pop(camera_id, None)
                self._global_store = collections.deque(
                    [e for e in self._global_store if e.camera_id != camera_id],
                    maxlen=self._global_store.maxlen,
                )
            else:
                self._store.clear()
                self._global_store.clear()


# Module-level singleton
event_store = EventStore()
