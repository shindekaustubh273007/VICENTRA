"""
Phase 2 — InferenceManager: singleton orchestrator for inference loops.

Mirrors the StreamManager pattern.  One shared YOLODetector instance
is lazily loaded and shared across all per-camera InferenceLoops.
"""

from typing import Dict, Optional, List

from app.services.detector import BaseDetector, YOLODetector
from app.services.inference_loop import InferenceLoop
from app.core.config import settings
from app.core.logging import logger


class InferenceManager:
    """
    Manages camera_id → InferenceLoop mappings.
    Lazily initialises a single shared detector on first start.
    """

    def __init__(self):
        self._loops: Dict[str, InferenceLoop] = {}
        self._detector: Optional[BaseDetector] = None
        self._enabled: bool = settings.AI_ENABLED

    # ── Detector lifecycle ───────────────────────────────────────────

    def _ensure_detector(self) -> bool:
        """Load the model once. Returns False if loading fails."""
        if self._detector is not None:
            return True
        try:
            self._detector = YOLODetector()
            return True
        except Exception as e:
            logger.error(f"Cannot initialise AI detector: {e}")
            return False

    # ── Loop lifecycle ───────────────────────────────────────────────

    def start_inference(self, camera_id: str) -> bool:
        """Start an inference loop for *camera_id*. Returns True on success."""
        if not self._enabled:
            logger.info(f"AI inference disabled — skipping camera {camera_id}")
            return False

        # Already running?
        existing = self._loops.get(camera_id)
        if existing and existing.status == "RUNNING":
            return False

        if not self._ensure_detector():
            return False

        loop = InferenceLoop(
            camera_id=camera_id,
            detector=self._detector,
            inference_fps=settings.AI_INFERENCE_FPS,
        )
        self._loops[camera_id] = loop
        loop.start()
        return True

    def stop_inference(self, camera_id: str) -> bool:
        """Stop inference for *camera_id*. Returns True if it was running."""
        loop = self._loops.get(camera_id)
        if not loop or loop.status == "STOPPED":
            return False
        loop.stop()
        return True

    def remove_inference(self, camera_id: str):
        """Stop and remove a loop entirely."""
        self.stop_inference(camera_id)
        self._loops.pop(camera_id, None)

    # ── Status ───────────────────────────────────────────────────────

    def get_status(self, camera_id: str) -> Optional[dict]:
        loop = self._loops.get(camera_id)
        if not loop:
            return None
        metrics = loop.get_metrics()
        if self._detector:
            metrics.update(self._detector.get_model_info())
        return metrics

    def get_all_status(self) -> dict:
        """
        Return a summary object with global AI info + per-camera metrics.
        """
        model_info = self._detector.get_model_info() if self._detector else {}
        per_camera = [loop.get_metrics() for loop in self._loops.values()]
        return {
            "ai_enabled": self._enabled,
            **model_info,
            "cameras": per_camera,
        }

    # ── Shutdown ─────────────────────────────────────────────────────

    def shutdown(self):
        """Stop all inference loops."""
        logger.info("Shutting down InferenceManager…")
        for loop in self._loops.values():
            loop.stop()
        self._loops.clear()


# Module-level singleton
inference_manager = InferenceManager()
