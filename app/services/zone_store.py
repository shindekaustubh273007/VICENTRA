"""
Phase 4 — Thread-safe store for active Virtual Zones.

Stores zones per camera for fast thread-safe access by evaluation loops.
"""

import threading
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime


@dataclass
class ZoneData:
    zone_id: str
    camera_id: str
    name: str
    zone_type: str                            # "restricted" or "monitoring"
    coordinates: List[Tuple[float, float]]     # List of (x, y) vertex points
    target_categories: List[str]               # ["person", "vehicle"], ["all"], etc.
    enabled: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def is_category_applicable(self, category: str) -> bool:
        if not self.target_categories or "all" in self.target_categories:
            return True
        return category in self.target_categories

    def to_dict(self) -> dict:
        return {
            "zone_id": self.zone_id,
            "camera_id": self.camera_id,
            "name": self.name,
            "zone_type": self.zone_type,
            "coordinates": [{"x": p[0], "y": p[1]} for p in self.coordinates],
            "target_categories": list(self.target_categories),
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ZoneStore:
    """
    Thread-safe in-memory cache of zones per camera.
    """
    def __init__(self):
        self._zones_by_id: Dict[str, ZoneData] = {}
        self._zones_by_camera: Dict[str, Dict[str, ZoneData]] = {}
        self._lock = threading.Lock()

    def set_zone(self, zone: ZoneData):
        with self._lock:
            self._zones_by_id[zone.zone_id] = zone
            if zone.camera_id not in self._zones_by_camera:
                self._zones_by_camera[zone.camera_id] = {}
            self._zones_by_camera[zone.camera_id][zone.zone_id] = zone

    def get_zone(self, zone_id: str) -> Optional[ZoneData]:
        with self._lock:
            return self._zones_by_id.get(zone_id)

    def get_zones_for_camera(self, camera_id: str, enabled_only: bool = True) -> List[ZoneData]:
        with self._lock:
            cam_zones = self._zones_by_camera.get(camera_id, {})
            if enabled_only:
                return [z for z in cam_zones.values() if z.enabled]
            return list(cam_zones.values())

    def get_all_zones(self) -> List[ZoneData]:
        with self._lock:
            return list(self._zones_by_id.values())

    def remove_zone(self, zone_id: str) -> Optional[ZoneData]:
        with self._lock:
            zone = self._zones_by_id.pop(zone_id, None)
            if zone:
                cam_zones = self._zones_by_camera.get(zone.camera_id)
                if cam_zones:
                    cam_zones.pop(zone_id, None)
            return zone

    def clear(self, camera_id: Optional[str] = None):
        with self._lock:
            if camera_id:
                cam_zones = self._zones_by_camera.pop(camera_id, {})
                for zid in cam_zones:
                    self._zones_by_id.pop(zid, None)
            else:
                self._zones_by_id.clear()
                self._zones_by_camera.clear()


# Module-level singleton
zone_store = ZoneStore()
