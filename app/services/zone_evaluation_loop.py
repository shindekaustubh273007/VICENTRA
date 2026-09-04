"""
Phase 4 — Per-camera Zone Evaluation Loop.

Polls TrackedStore for active object tracks, evaluates position against
configured Virtual Zones using ray-casting geometry, manages state transitions
(Outside ↔ Inside), emits ENTER, EXIT, and INTRUSION events, and cleans up
expired track state automatically.
"""

import uuid
import threading
import time
from typing import Dict, Tuple, Set, Optional
from datetime import datetime

from app.core.logging import logger
from app.core.config import settings
from app.services.tracked_store import tracked_store
from app.services.zone_store import zone_store, ZoneData
from app.services.event_store import event_store, ZoneEvent
from app.services.zone_geometry import point_in_polygon, get_evaluation_point


class ZoneEvaluationLoop:
    """
    Daemon thread that continuously evaluates active tracks for a camera
    against all enabled virtual zones for that camera.
    """

    def __init__(
        self,
        camera_id: str,
        evaluation_fps: float = None,
    ):
        self.camera_id = camera_id
        self.evaluation_fps = evaluation_fps or settings.ZONE_EVALUATION_FPS

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # State tracking: (zone_id, track_id) -> is_inside (bool)
        self.zone_states: Dict[Tuple[str, str], bool] = {}

        self.status: str = "STOPPED"
        self.evaluations_count: int = 0
        self.events_emitted_count: int = 0

    def start(self):
        if self._thread and self._thread.is_alive():
            logger.warning(f"Zone evaluation loop for {self.camera_id} already running.")
            return

        self._stop_event.clear()
        self.status = "RUNNING"
        self._thread = threading.Thread(
            target=self._run,
            name=f"ZoneEval-{self.camera_id}",
            daemon=True,
        )
        self._thread.start()
        logger.info(f"Zone evaluation loop started for camera {self.camera_id}")

    def stop(self):
        self.status = "STOPPED"
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3.0)
        self.zone_states.clear()
        logger.info(f"Zone evaluation loop stopped for camera {self.camera_id}")

    def _run(self):
        interval = 1.0 / self.evaluation_fps if self.evaluation_fps > 0 else 0.2

        while not self._stop_event.is_set():
            loop_start = time.time()
            try:
                self._evaluate_step()
            except Exception as e:
                logger.error(f"Zone evaluation error for camera {self.camera_id}: {e}")

            elapsed = time.time() - loop_start
            sleep_time = max(0, interval - elapsed)
            if sleep_time > 0:
                self._stop_event.wait(timeout=sleep_time)

    def _evaluate_step(self):
        active_tracks = tracked_store.get_tracks(self.camera_id)
        active_zones = zone_store.get_zones_for_camera(self.camera_id, enabled_only=True)

        active_track_ids: Set[str] = {t.track_id for t in active_tracks}

        # 1. State cleanup: remove states for tracks that no longer exist
        stale_keys = [
            (zid, tid)
            for (zid, tid) in self.zone_states.keys()
            if tid not in active_track_ids
        ]
        for key in stale_keys:
            del self.zone_states[key]

        if not active_tracks or not active_zones:
            return

        self.evaluations_count += 1
        now = datetime.now()

        # 2. Evaluate each track against each zone
        for track in active_tracks:
            # Position evaluation point (bottom-center for ground plane)
            pos = get_evaluation_point(track.current_bounding_box, mode="bottom_center")

            for zone in active_zones:
                # Check category filtering
                if not (
                    zone.is_category_applicable(track.category)
                    or zone.is_category_applicable(track.class_name)
                ):
                    continue

                currently_inside = point_in_polygon(pos, zone.coordinates)
                state_key = (zone.zone_id, track.track_id)
                was_inside = self.zone_states.get(state_key, False)

                # State transition evaluation
                if not was_inside and currently_inside:
                    # Transition: Outside -> Inside
                    self.zone_states[state_key] = True

                    # 1. Emit ENTER event
                    enter_event = ZoneEvent(
                        event_id=str(uuid.uuid4())[:8],
                        event_type="ENTER",
                        camera_id=self.camera_id,
                        zone_id=zone.zone_id,
                        zone_name=zone.name,
                        track_id=track.track_id,
                        object_class=track.class_name,
                        category=track.category,
                        timestamp=now,
                        position=pos,
                    )
                    event_store.add_event(enter_event)
                    self.events_emitted_count += 1
                    logger.info(
                        f"[ZONE EVENT] ENTER: Track {track.track_id} ({track.class_name}) "
                        f"entered zone '{zone.name}' on camera {self.camera_id}"
                    )

                    # 2. If restricted zone, also emit INTRUSION event
                    if zone.zone_type == "restricted":
                        intrusion_event = ZoneEvent(
                            event_id=str(uuid.uuid4())[:8],
                            event_type="INTRUSION",
                            camera_id=self.camera_id,
                            zone_id=zone.zone_id,
                            zone_name=zone.name,
                            track_id=track.track_id,
                            object_class=track.class_name,
                            category=track.category,
                            timestamp=now,
                            position=pos,
                        )
                        event_store.add_event(intrusion_event)
                        self.events_emitted_count += 1
                        logger.warning(
                            f"[SECURITY INTRUSION] Track {track.track_id} ({track.class_name}) "
                            f"intruded into restricted zone '{zone.name}' on camera {self.camera_id}!"
                        )

                elif was_inside and not currently_inside:
                    # Transition: Inside -> Outside
                    self.zone_states[state_key] = False

                    exit_event = ZoneEvent(
                        event_id=str(uuid.uuid4())[:8],
                        event_type="EXIT",
                        camera_id=self.camera_id,
                        zone_id=zone.zone_id,
                        zone_name=zone.name,
                        track_id=track.track_id,
                        object_class=track.class_name,
                        category=track.category,
                        timestamp=now,
                        position=pos,
                    )
                    event_store.add_event(exit_event)
                    self.events_emitted_count += 1
                    logger.info(
                        f"[ZONE EVENT] EXIT: Track {track.track_id} ({track.class_name}) "
                        f"exited zone '{zone.name}' on camera {self.camera_id}"
                    )

                # Continuous inside presence (was_inside and currently_inside):
                # NO new events emitted! (Deduplication requirement met).

    def get_metrics(self) -> dict:
        return {
            "camera_id": self.camera_id,
            "status": self.status,
            "evaluations_count": self.evaluations_count,
            "events_emitted_count": self.events_emitted_count,
            "active_zone_states": len(self.zone_states),
        }
