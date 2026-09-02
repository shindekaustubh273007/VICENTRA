"""
Phase 2 — Per-camera inference loop.

Polls FrameProvider, skips duplicates, runs the detector, stores results,
and tracks performance metrics. One daemon thread per active camera.
"""

import threading
import time
from typing import Optional
from datetime import datetime

from app.core.logging import logger
from app.services.detector import BaseDetector, Detection, RawDetection
from app.services.result_store import result_store
from app.services.provider import provider


class InferenceLoop:
    """
    Daemon thread that continuously pulls frames from FrameProvider,
    runs them through a detector, and pushes results into the ResultStore.
    """

    def __init__(
        self,
        camera_id: str,
        detector: BaseDetector,
        inference_fps: float = 2.0,
    ):
        self.camera_id = camera_id
        self.detector = detector
        self.inference_fps = inference_fps

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_timestamp: Optional[datetime] = None

        # ── Metrics ──
        self.frames_processed: int = 0
        self.frames_skipped: int = 0
        self.total_detections: int = 0
        self.average_inference_ms: float = 0.0
        self.inference_fps_actual: float = 0.0
        self.detections_per_class: dict = {}
        self.status: str = "STOPPED"

        self._inference_times: list = []
        self._fps_window: list = []
        self._fps_window_size: int = 30

    # ── Lifecycle ────────────────────────────────────────────────────

    def start(self):
        if self._thread and self._thread.is_alive():
            logger.warning(
                f"Inference loop for {self.camera_id} already running."
            )
            return

        self._stop_event.clear()
        self.status = "RUNNING"
        self._thread = threading.Thread(
            target=self._run,
            name=f"Inference-{self.camera_id}",
            daemon=True,
        )
        self._thread.start()
        logger.info(f"Inference loop started for camera {self.camera_id}")

    def stop(self):
        self.status = "STOPPED"
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3.0)
        logger.info(f"Inference loop stopped for camera {self.camera_id}")

    # ── Main loop ────────────────────────────────────────────────────

    def _run(self):
        interval = 1.0 / self.inference_fps if self.inference_fps > 0 else 1.0

        while not self._stop_event.is_set():
            loop_start = time.time()

            try:
                frame_data = provider.get_latest_frame(self.camera_id)

                if frame_data is None:
                    self._stop_event.wait(timeout=0.1)
                    continue

                # Skip duplicate frames (same timestamp = same frame)
                if (
                    self._last_timestamp is not None
                    and frame_data.timestamp == self._last_timestamp
                ):
                    self.frames_skipped += 1
                    self._stop_event.wait(timeout=0.05)
                    continue

                self._last_timestamp = frame_data.timestamp

                # Run inference
                infer_start = time.time()
                raw_detections: list[RawDetection] = self.detector.detect(
                    frame_data.frame
                )
                infer_ms = (time.time() - infer_start) * 1000.0

                # Convert RawDetection → Detection (add camera context)
                frame_ts_str = frame_data.timestamp.isoformat()
                detections: list[Detection] = [
                    Detection(
                        camera_id=self.camera_id,
                        timestamp=frame_data.timestamp,
                        frame_timestamp=frame_ts_str,
                        class_id=rd.class_id,
                        class_name=rd.class_name,
                        category=rd.category,
                        confidence=rd.confidence,
                        bounding_box=rd.bounding_box,
                    )
                    for rd in raw_detections
                ]

                # Store results
                if detections:
                    result_store.add_detections(self.camera_id, detections)

                # Update metrics
                self.frames_processed += 1
                self.total_detections += len(detections)
                self._update_inference_time(infer_ms)
                self._update_fps(time.time())

                for d in detections:
                    self.detections_per_class[d.class_name] = (
                        self.detections_per_class.get(d.class_name, 0) + 1
                    )

            except Exception as e:
                logger.error(
                    f"Inference error for camera {self.camera_id}: {e}"
                )

            # Throttle to target inference FPS
            elapsed = time.time() - loop_start
            sleep_time = max(0, interval - elapsed)
            if sleep_time > 0:
                self._stop_event.wait(timeout=sleep_time)

    # ── Metric helpers ───────────────────────────────────────────────

    def _update_inference_time(self, ms: float):
        self._inference_times.append(ms)
        if len(self._inference_times) > 100:
            self._inference_times.pop(0)
        self.average_inference_ms = round(
            sum(self._inference_times) / len(self._inference_times), 1
        )

    def _update_fps(self, current_time: float):
        self._fps_window.append(current_time)
        if len(self._fps_window) > self._fps_window_size:
            self._fps_window.pop(0)
        if len(self._fps_window) > 1:
            diff = self._fps_window[-1] - self._fps_window[0]
            if diff > 0:
                self.inference_fps_actual = round(
                    (len(self._fps_window) - 1) / diff, 1
                )

    def get_metrics(self) -> dict:
        return {
            "camera_id": self.camera_id,
            "status": self.status,
            "frames_processed": self.frames_processed,
            "frames_skipped": self.frames_skipped,
            "total_detections": self.total_detections,
            "average_inference_ms": self.average_inference_ms,
            "inference_fps": self.inference_fps_actual,
            "detections_per_class": dict(self.detections_per_class),
        }
