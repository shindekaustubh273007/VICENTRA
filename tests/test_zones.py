"""
Unit and Integration tests for Phase 4 Virtual Fences, Zones & Intrusion Detection.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.services.detector import BoundingBox, Detection
from app.services.tracker import TrackedObject
from app.services.zone_geometry import point_in_polygon, get_evaluation_point
from app.services.zone_store import ZoneData, ZoneStore, zone_store
from app.services.event_store import ZoneEvent, EventStore, event_store
from app.services.zone_evaluation_loop import ZoneEvaluationLoop
from app.services.tracked_store import tracked_store
from app.main import app


# ── 1. Geometry & Evaluation Point Tests ───────────────────────────────

def test_point_in_polygon():
    # Square polygon (0,0) -> (100,0) -> (100,100) -> (0,100)
    poly = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]

    # Inside
    assert point_in_polygon((50.0, 50.0), poly) is True
    # Outside
    assert point_in_polygon((150.0, 50.0), poly) is False
    assert point_in_polygon((-10.0, 50.0), poly) is False
    assert point_in_polygon((50.0, 150.0), poly) is False

    # Triangle
    tri = [(0.0, 0.0), (100.0, 0.0), (50.0, 100.0)]
    assert point_in_polygon((50.0, 30.0), tri) is True
    assert point_in_polygon((50.0, 120.0), tri) is False


def test_get_evaluation_point():
    box = BoundingBox(x1=100.0, y1=200.0, x2=200.0, y2=400.0)

    # Bottom-center: ((100+200)/2, 400) = (150, 400)
    bc = get_evaluation_point(box, mode="bottom_center")
    assert bc == (150.0, 400.0)

    # Centroid: ((100+200)/2, (200+400)/2) = (150, 300)
    c = get_evaluation_point(box, mode="centroid")
    assert c == (150.0, 300.0)


# ── 2. Zone Evaluation State Transition & Deduplication ────────────────

def test_zone_state_transition_sequence():
    """
    Mandatory transition test:
    OUTSIDE -> OUTSIDE -> INSIDE -> INSIDE -> INSIDE -> OUTSIDE
    Expected: ENTER x 1, INTRUSION x 1, EXIT x 1. No duplicate events!
    """
    cam_id = "CAM-TRANSITION-TEST"
    test_event_store = EventStore(max_per_camera=100)

    zone = ZoneData(
        zone_id="Z1",
        camera_id=cam_id,
        name="Restricted Area",
        zone_type="restricted",
        coordinates=[(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)],
        target_categories=["all"],
        enabled=True,
    )
    zone_store.set_zone(zone)

    loop = ZoneEvaluationLoop(camera_id=cam_id, evaluation_fps=10.0)

    # Helper to create a fake TrackedObject with bottom-center at (x, y)
    def make_track(track_id: str, cx: float, cy: float) -> TrackedObject:
        det = Detection(
            camera_id=cam_id,
            timestamp=datetime.now(),
            frame_timestamp="ts",
            class_id=0,
            class_name="person",
            category="person",
            confidence=0.9,
            bounding_box=BoundingBox(x1=cx - 10, y1=cy - 20, x2=cx + 10, y2=cy),
        )
        return TrackedObject(track_id=track_id, camera_id=cam_id, initial_detection=det)

    event_store.clear(cam_id)

    # Frame 1: OUTSIDE (150, 150)
    t1 = make_track("T1", 150.0, 150.0)
    tracked_store.update_tracks(cam_id, [t1])
    loop._evaluate_step()
    assert len(event_store.get_events(cam_id)) == 0

    # Frame 2: OUTSIDE (120, 120)
    t2 = make_track("T1", 120.0, 120.0)
    tracked_store.update_tracks(cam_id, [t2])
    loop._evaluate_step()
    assert len(event_store.get_events(cam_id)) == 0

    # Frame 3: INSIDE (50, 50) -> TRANSITION: Emit ENTER & INTRUSION
    t3 = make_track("T1", 50.0, 50.0)
    tracked_store.update_tracks(cam_id, [t3])
    loop._evaluate_step()
    events_f3 = event_store.get_events(cam_id)
    assert len(events_f3) == 2
    types_f3 = [e.event_type for e in events_f3]
    assert "ENTER" in types_f3
    assert "INTRUSION" in types_f3

    # Frame 4: INSIDE (40, 40) -> REMAIN INSIDE -> NO NEW EVENTS!
    t4 = make_track("T1", 40.0, 40.0)
    tracked_store.update_tracks(cam_id, [t4])
    loop._evaluate_step()
    assert len(event_store.get_events(cam_id)) == 2

    # Frame 5: INSIDE (30, 30) -> REMAIN INSIDE -> NO NEW EVENTS!
    t5 = make_track("T1", 30.0, 30.0)
    tracked_store.update_tracks(cam_id, [t5])
    loop._evaluate_step()
    assert len(event_store.get_events(cam_id)) == 2

    # Frame 6: OUTSIDE (150, 150) -> TRANSITION: Emit EXIT
    t6 = make_track("T1", 150.0, 150.0)
    tracked_store.update_tracks(cam_id, [t6])
    loop._evaluate_step()
    events_f6 = event_store.get_events(cam_id)
    assert len(events_f6) == 3
    assert events_f6[-1].event_type == "EXIT"

    # Cleanup
    zone_store.clear(cam_id)
    event_store.clear(cam_id)
    tracked_store.clear(cam_id)


def test_track_expiry_state_cleanup():
    """Verify state cleanup for expired tracks."""
    cam_id = "CAM-CLEANUP-TEST"
    loop = ZoneEvaluationLoop(camera_id=cam_id)

    zone = ZoneData(
        zone_id="Z1",
        camera_id=cam_id,
        name="Zone1",
        zone_type="monitoring",
        coordinates=[(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)],
        target_categories=["all"],
        enabled=True,
    )
    zone_store.set_zone(zone)

    det = Detection(cam_id, datetime.now(), "ts", 0, "person", "person", 0.9, BoundingBox(0,0,10,10))
    t1 = TrackedObject("T-EXP", cam_id, det)

    tracked_store.update_tracks(cam_id, [t1])
    loop._evaluate_step()

    # State key should exist
    assert ("Z1", "T-EXP") in loop.zone_states

    # Frame 2: Track expires / is removed from tracked_store
    tracked_store.update_tracks(cam_id, [])
    loop._evaluate_step()

    # State key must be cleaned up!
    assert ("Z1", "T-EXP") not in loop.zone_states

    zone_store.clear(cam_id)
    tracked_store.clear(cam_id)


def test_category_filtering():
    """Zone configured for 'person' ignores 'car' tracks."""
    cam_id = "CAM-CAT-TEST"
    event_store.clear(cam_id)

    zone = ZoneData(
        zone_id="Z-PERSON",
        camera_id=cam_id,
        name="Pedestrian Walkway",
        zone_type="restricted",
        coordinates=[(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)],
        target_categories=["person"],
        enabled=True,
    )
    zone_store.set_zone(zone)
    loop = ZoneEvaluationLoop(camera_id=cam_id)

    # Car detection inside zone
    det_car = Detection(cam_id, datetime.now(), "ts", 2, "car", "vehicle", 0.9, BoundingBox(0,0,10,10))
    t_car = TrackedObject("T-CAR", cam_id, det_car)

    tracked_store.update_tracks(cam_id, [t_car])
    loop._evaluate_step()

    # Car must NOT trigger events for person-only zone
    assert len(event_store.get_events(cam_id)) == 0

    # Person detection inside zone
    det_person = Detection(cam_id, datetime.now(), "ts", 0, "person", "person", 0.9, BoundingBox(0,0,10,10))
    t_person = TrackedObject("T-PERSON", cam_id, det_person)

    tracked_store.update_tracks(cam_id, [t_person])
    loop._evaluate_step()

    # Person MUST trigger events
    assert len(event_store.get_events(cam_id)) == 2

    zone_store.clear(cam_id)
    event_store.clear(cam_id)
    tracked_store.clear(cam_id)


def test_multi_camera_isolation():
    """Tracks on Camera A must not evaluate against zones on Camera B."""
    cam_a = "CAM-A"
    cam_b = "CAM-B"

    event_store.clear()
    zone_store.clear()

    zone_b = ZoneData(
        zone_id="ZB",
        camera_id=cam_b,
        name="Zone B",
        zone_type="restricted",
        coordinates=[(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)],
        target_categories=["all"],
        enabled=True,
    )
    zone_store.set_zone(zone_b)

    loop_a = ZoneEvaluationLoop(camera_id=cam_a)

    det_a = Detection(cam_a, datetime.now(), "ts", 0, "person", "person", 0.9, BoundingBox(0,0,10,10))
    t_a = TrackedObject("T-A", cam_a, det_a)
    tracked_store.update_tracks(cam_a, [t_a])

    loop_a._evaluate_step()

    # Zero events generated on Camera A or B
    assert len(event_store.get_events(cam_a)) == 0
    assert len(event_store.get_events(cam_b)) == 0

    zone_store.clear()
    event_store.clear()
    tracked_store.clear()


# ── 3. API Endpoint Tests ──────────────────────────────────────────────

def test_zone_crud_and_events_api():
    client = TestClient(app)

    # 1. Create Camera
    client.post(
        "/api/cameras/",
        json={
            "camera_id": "API-ZONE-CAM",
            "name": "Perimeter Cam",
            "location": "Fence",
            "source_type": "file",
            "source_url": "test.mp4",
            "enabled": False,
        },
    )

    # 2. Create Zone
    res_create = client.post(
        "/api/cameras/API-ZONE-CAM/zones",
        json={
            "name": "Forbidden Gate",
            "zone_type": "restricted",
            "coordinates": [{"x": 10.0, "y": 10.0}, {"x": 200.0, "y": 10.0}, {"x": 200.0, "y": 200.0}],
            "target_categories": ["person"],
            "enabled": True,
        },
    )
    assert res_create.status_code == 201, res_create.text
    zdata = res_create.json()
    zone_id = zdata["zone_id"]
    assert zdata["name"] == "Forbidden Gate"

    # 3. List Zones for Camera
    res_list = client.get("/api/cameras/API-ZONE-CAM/zones")
    assert res_list.status_code == 200
    assert res_list.json()["count"] == 1

    # 4. Get Zone
    res_get = client.get(f"/api/zones/{zone_id}")
    assert res_get.status_code == 200
    assert res_get.json()["zone_id"] == zone_id

    # 5. Update Zone
    res_put = client.put(
        f"/api/zones/{zone_id}",
        json={"name": "Updated Forbidden Gate", "zone_type": "monitoring"},
    )
    assert res_put.status_code == 200
    assert res_put.json()["name"] == "Updated Forbidden Gate"
    assert res_put.json()["zone_type"] == "monitoring"

    # 6. Query Events Endpoint
    res_events = client.get("/api/events")
    assert res_events.status_code == 200
    assert "events" in res_events.json()

    # 7. Invalid Zone Creation (less than 3 points)
    res_invalid = client.post(
        "/api/cameras/API-ZONE-CAM/zones",
        json={
            "name": "Invalid Zone",
            "coordinates": [{"x": 0.0, "y": 0.0}, {"x": 10.0, "y": 10.0}],
        },
    )
    assert res_invalid.status_code == 422

    # 8. Delete Zone
    res_del = client.delete(f"/api/zones/{zone_id}")
    assert res_del.status_code == 204
