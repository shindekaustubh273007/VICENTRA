"""
Phase 2 — AI Detector abstraction and YOLO implementation.

BaseDetector provides the interface. YOLODetector is the concrete
implementation using Ultralytics YOLO for person/vehicle detection.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

from app.core.config import settings
from app.core.logging import logger


# ─── Data Structures ────────────────────────────────────────────────

@dataclass
class BoundingBox:
    """Axis-aligned bounding box in pixel coordinates."""
    x1: float
    y1: float
    x2: float
    y2: float

    def to_dict(self) -> dict:
        return {"x1": self.x1, "y1": self.y1, "x2": self.x2, "y2": self.y2}


@dataclass
class RawDetection:
    """
    Model-level detection output — no camera context.
    Returned by BaseDetector.detect().
    """
    class_id: int
    class_name: str
    category: str
    confidence: float
    bounding_box: BoundingBox


@dataclass
class Detection:
    """
    Full detection with camera context.
    Produced by InferenceLoop from RawDetection + FrameData metadata.
    """
    camera_id: str
    timestamp: datetime
    frame_timestamp: str        # ISO-format string used as frame identifier
    class_id: int
    class_name: str
    category: str               # "person" or "vehicle"
    confidence: float
    bounding_box: BoundingBox

    def to_dict(self) -> dict:
        return {
            "camera_id": self.camera_id,
            "timestamp": self.timestamp.isoformat(),
            "frame_timestamp": self.frame_timestamp,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "category": self.category,
            "confidence": round(self.confidence, 4),
            "bounding_box": self.bounding_box.to_dict(),
        }


# ─── Class / Category Maps ──────────────────────────────────────────

SUPPORTED_CLASSES: Dict[int, str] = {
    0: "person",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

CATEGORY_MAP: Dict[str, str] = {
    "person": "person",
    "car": "vehicle",
    "motorcycle": "vehicle",
    "bus": "vehicle",
    "truck": "vehicle",
}


# ─── Abstract Base ──────────────────────────────────────────────────

class BaseDetector(ABC):
    """Interface that every detector must implement."""

    @abstractmethod
    def detect(self, frame: np.ndarray) -> List[RawDetection]:
        """Run inference on a single BGR frame and return raw detections."""
        ...

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Return metadata about the loaded model and its configuration."""
        ...


# ─── YOLO Implementation ────────────────────────────────────────────

class YOLODetector(BaseDetector):
    """
    Concrete detector backed by Ultralytics YOLOv8.

    * Filters results to SUPPORTED_CLASSES only.
    * Auto-selects CUDA when available, falls back to CPU.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: Optional[str] = None,
        confidence_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
    ):
        self.model_path = model_path or settings.AI_MODEL
        self.confidence_threshold = (
            confidence_threshold if confidence_threshold is not None
            else settings.AI_CONFIDENCE_THRESHOLD
        )
        self.iou_threshold = (
            iou_threshold if iou_threshold is not None
            else settings.AI_IOU_THRESHOLD
        )

        # ── Device selection ──
        self.device = self._resolve_device(device)
        logger.info(
            f"AI Detector initializing: model={self.model_path}, device={self.device}"
        )

        # ── Load model ──
        try:
            from ultralytics import YOLO

            self.model = YOLO(self.model_path)
            self.model.to(self.device)
            logger.info(f"AI Detector ready on device: {self.device}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model '{self.model_path}': {e}")
            raise

        self._supported_class_ids = list(SUPPORTED_CLASSES.keys())

    # ── public ───────────────────────────────────────────────────────

    def detect(self, frame: np.ndarray) -> List[RawDetection]:
        if frame is None or frame.size == 0:
            return []

        try:
            results = self.model(
                frame,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                verbose=False,
                classes=self._supported_class_ids,
            )
        except Exception as e:
            logger.error(f"YOLO inference error: {e}")
            return []

        detections: List[RawDetection] = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                class_id = int(box.cls[0].item())
                if class_id not in SUPPORTED_CLASSES:
                    continue

                class_name = SUPPORTED_CLASSES[class_id]
                category = CATEGORY_MAP[class_name]
                confidence = float(box.conf[0].item())
                coords = box.xyxy[0].tolist()

                detections.append(
                    RawDetection(
                        class_id=class_id,
                        class_name=class_name,
                        category=category,
                        confidence=confidence,
                        bounding_box=BoundingBox(
                            x1=coords[0],
                            y1=coords[1],
                            x2=coords[2],
                            y2=coords[3],
                        ),
                    )
                )

        return detections

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_path,
            "selected_device": self.device,
            "confidence_threshold": self.confidence_threshold,
            "iou_threshold": self.iou_threshold,
        }

    # ── private ──────────────────────────────────────────────────────

    @staticmethod
    def _resolve_device(requested: Optional[str]) -> str:
        """Pick the best available device."""
        if requested and requested != "auto":
            return requested

        device_cfg = settings.AI_DEVICE
        if device_cfg != "auto":
            return device_cfg

        try:
            import torch

            if torch.cuda.is_available():
                logger.info("CUDA detected — using GPU for inference.")
                return "cuda"
        except ImportError:
            pass

        logger.info("CUDA not available — falling back to CPU.")
        return "cpu"
