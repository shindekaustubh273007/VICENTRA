"""
Phase 4 — ZoneManager: singleton orchestrator for zone evaluation loops.

Mirrors StreamManager, InferenceManager, and TrackingManager patterns.
"""

import json
from typing import Dict, Optional, List

from app.core.config import settings
from app.core.logging import logger
from app.services.zone_evaluation_loop import ZoneEvaluationLoop
from app.services.zone_store import zone_store, ZoneData
from app.services.event_store import event_store


class ZoneManager:
    """
    Orchestrates per-camera ZoneEvaluationLoops.
    """

    def __init__(self):
        self._loops: Dict[str, ZoneEvaluationLoop] = {}
        self._enabled: bool = settings.ZONES_ENABLED

    def load_zones_from_db(self):
        """Loads persistent zones from database into zone_store."""
        try:
            from app.database.database import SessionLocal
            from app.database import models

            db = SessionLocal()
            try:
                db_zones = db.query(models.Zone).all()
                for z in db_zones:
                    try:
                        coords = json.loads(z.coordinates_json)
                        coords_tuples = [(float(p["x"]), float(p["y"])) for p in coords]
                        cats = json.loads(z.target_categories_json) if z.target_categories_json else ["all"]
                    except Exception as err:
                        logger.error(f"Failed parsing DB zone {z.zone_id}: {err}")
                        continue

                    zone_data = ZoneData(
                        zone_id=z.zone_id,
                        camera_id=z.camera_id,
                        name=z.name,
                        zone_type=z.zone_type,
                        coordinates=coords_tuples,
                        target_categories=cats,
                        enabled=z.enabled,
                        created_at=z.created_at,
                        updated_at=z.updated_at,
                    )
                    zone_store.set_zone(zone_data)
                logger.info(f"Loaded {len(db_zones)} virtual zones from database.")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error loading zones from DB: {e}")

    def start_zone_evaluation(self, camera_id: str) -> bool:
        if not self._enabled:
            logger.info(f"Zone evaluation disabled — skipping camera {camera_id}")
            return False

        existing = self._loops.get(camera_id)
        if existing and existing.status == "RUNNING":
            return False

        loop = ZoneEvaluationLoop(camera_id=camera_id)
        self._loops[camera_id] = loop
        loop.start()
        return True

    def stop_zone_evaluation(self, camera_id: str) -> bool:
        loop = self._loops.get(camera_id)
        if not loop or loop.status == "STOPPED":
            return False
        loop.stop()
        return True

    def remove_zone_evaluation(self, camera_id: str):
        self.stop_zone_evaluation(camera_id)
        self._loops.pop(camera_id, None)
        zone_store.clear(camera_id)
        event_store.clear(camera_id)

    def get_status(self, camera_id: str) -> Optional[dict]:
        loop = self._loops.get(camera_id)
        if not loop:
            return None
        return loop.get_metrics()

    def get_all_status(self) -> dict:
        per_camera = [loop.get_metrics() for loop in self._loops.values()]
        return {
            "zones_enabled": self._enabled,
            "cameras": per_camera,
        }

    def shutdown(self):
        logger.info("Shutting down ZoneManager…")
        for loop in self._loops.values():
            loop.stop()
        self._loops.clear()


# Module-level singleton
zone_manager = ZoneManager()
