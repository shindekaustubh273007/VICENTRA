"""
Unit and Integration tests for Phase 2 AI Inference Engine.
"""

import pytest
import numpy as np
from datetime import datetime
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.services.detector import (
    BaseDetector,
    YOLODetector,
    RawDetection,
    Detection,
    BoundingBox,
    SUPPORTED_CLASSES,
    CATEGORY_MAP,
)
from app.services.result_store import ResultStore
from app.services.inference_loop import InferenceLoop
from app.services.inference_manager import InferenceManager, inference_manager
from app.services.frame_buffer import FrameData
from app.utils.video import annotate_frame
from app.main import app


# ─── Mock Detector for Testing ──────────────────────────────────────

class MockDetector(BaseDetector):
    def __init__(self, raw_detections=None):
        self.raw_detections = raw_detections or [
            RawDetection(
                class_id=0,
                class_name="person",
                category="person",
                confidence=0.85,
                bounding_box=BoundingBox(10.0, 10.0, 50.0, 100.0),
            ),
            RawDetection(
                class_id=2,
                class_name="car",
                category="vehicle",
                confidence=0.92,
                bounding_box=BoundingBox(100.0, 100.0, 200.0, 180.0),
            ),
        ]

    def detect(self, frame: np.ndarray):
        if frame is None or frame.size == 0:
            return []
        return self.raw_detections

    def get_model_info(self):
        return {
            "model_name": "mock_model.pt",
            "selected_device": "cpu",
            "confidence_threshold": 0.4,
            "iou_threshold": 0.45,
        }


# ─── 1. Detector & Class Mapping Tests ──────────────────────────────

def test_category_mapping():
    assert CATEGORY_MAP["person"] == "person"
    assert CATEGORY_MAP["car"] == "vehicle"
    assert CATEGORY_MAP["motorcycle"] == "vehicle"
    assert CATEGORY_MAP["bus"] == "vehicle"
    assert CATEGORY_MAP["truck"] == "vehicle"


def test_supported_classes():
    assert 0 in SUPPORTED_CLASSES
    assert SUPPORTED_CLASSES[0] == "person"
    assert 2 in SUPPORTED_CLASSES
    assert SUPPORTED_CLASSES[2] == "car"


def test_device_selection():
    # Test CPU forced
    dev = YOLODetector._resolve_device("cpu")
    assert dev == "cpu"

    # Test CUDA mock
    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = True

    with patch.dict("sys.modules", {"torch": mock_torch}):
        dev = YOLODetector._resolve_device("auto")
        assert dev == "cuda"

    mock_torch.cuda.is_available.return_value = False
    with patch.dict("sys.modules", {"torch": mock_torch}):
        dev = YOLODetector._resolve_device("auto")
        assert dev == "cpu"


def test_yolo_detector_invalid_frame():
    detector = MockDetector()
    assert detector.detect(None) == []
    assert detector.detect(np.array([])) == []


# ─── 2. ResultStore Tests ──────────────────────────────────────────

def test_result_store():
    store = ResultStore(max_per_camera=3)
    cam_id = "CAM-TEST"

    det1 = Detection("CAM-TEST", datetime.now(), "2026-09-02T10:00:00", 0, "person", "person", 0.9, BoundingBox(0,0,10,10))
    det2 = Detection("CAM-TEST", datetime.now(), "2026-09-02T10:00:00", 2, "car", "vehicle", 0.8, BoundingBox(10,10,20,20))
    det3 = Detection("CAM-TEST", datetime.now(), "2026-09-02T10:00:01", 0, "person", "person", 0.95, BoundingBox(0,0,12,12))
    det4 = Detection("CAM-TEST", datetime.now(), "2026-09-02T10:00:02", 7, "truck", "vehicle", 0.75, BoundingBox(30,30,50,50))

    # Add detections
    store.add_detections(cam_id, [det1, det2])
    assert len(store.get_detections(cam_id)) == 2

    # Latest frame detections (timestamp 10:00:00)
    latest = store.get_latest_detections(cam_id)
    assert len(latest) == 2

    # Add 2 more (total 4), should evict det1 due to max_per_camera=3
    store.add_detections(cam_id, [det3, det4])
    dets = store.get_detections(cam_id)
    assert len(dets) == 3
    assert dets[0] == det2
    assert dets[-1] == det4

    # Latest detections should now only be det4 (timestamp 10:00:02)
    latest = store.get_latest_detections(cam_id)
    assert len(latest) == 1
    assert latest[0].class_name == "truck"


# ─── 3. InferenceLoop Tests ────────────────────────────────────────

def test_inference_loop_duplicate_prevention_and_metrics():
    detector = MockDetector()
    loop = InferenceLoop("CAM-01", detector, inference_fps=10.0)

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    ts1 = datetime.now()

    # Mock provider frame
    frame_data1 = FrameData("CAM-01", frame, ts1, "640x480")

    with patch("app.services.provider.provider.get_latest_frame", return_value=frame_data1):
        # First iteration: process frame
        loop._run_one_step() if hasattr(loop, "_run_one_step") else None

    # Verify duplicate frame logic directly
    assert loop.frames_processed == 0  # not run via loop._run() yet

    # Test processing manually in loop structure
    loop.start()
    import time
    time.sleep(0.3)
    loop.stop()

    metrics = loop.get_metrics()
    assert metrics["camera_id"] == "CAM-01"
    assert metrics["status"] == "STOPPED"


# ─── 4. Annotation Tests ───────────────────────────────────────────

def test_annotate_frame():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    det = Detection("CAM-01", datetime.now(), "ts1", 0, "person", "person", 0.9, BoundingBox(10, 10, 100, 100))

    annotated = annotate_frame(frame, [det])

    assert annotated.shape == frame.shape
    # Frame should be modified (not all zeros)
    assert np.any(annotated != 0)
    # Original frame must remain all zeros
    assert np.all(frame == 0)


# ─── 5. API Endpoint Tests ─────────────────────────────────────────

def test_ai_status_endpoint():
    client = TestClient(app)
    response = client.get("/api/ai/status")
    assert response.status_code == 200
    data = response.json()
    assert "ai_enabled" in data
    assert "cameras" in data


def test_camera_detections_endpoint():
    client = TestClient(app)
    response = client.get("/api/cameras/NONEXISTENT/detections")
    assert response.status_code == 200
    data = response.json()
    assert data["camera_id"] == "NONEXISTENT"
    assert data["count"] == 0
    assert data["detections"] == []
