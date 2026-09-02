import threading
import time
import cv2
from datetime import datetime
from typing import Optional

from app.core.logging import logger
from app.services.frame_buffer import FrameBuffer, FrameData
from app.services.frame_sampler import FrameSampler
from app.utils.video import parse_source
from app.core.config import settings

class StreamWorker:
    """
    Independent worker thread that reads a video stream using OpenCV,
    applies sampling, and pushes to a FrameBuffer.
    Handles disconnections and automatic exponential backoff reconnection.
    """
    def __init__(self, camera_id: str, source_type: str, source_url: str, 
                 target_fps: int, buffer_size: int):
        self.camera_id = camera_id
        self.source_type = source_type
        self.source_url = source_url
        
        self.frame_buffer = FrameBuffer(max_size=buffer_size)
        self.sampler = FrameSampler(target_fps=target_fps)
        
        self.status = "STOPPED"
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        
        # Health metrics
        self.current_fps = 0.0
        self.target_fps = target_fps
        self.resolution = "--"
        self.frames_received = 0
        self.frames_sampled = 0
        self.frames_dropped = 0
        self.reconnections = 0
        self.last_frame_timestamp: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self._start_time = 0.0
        
        # FPS calculation window
        self._fps_window = []
        self._fps_window_size = 30

    def start(self):
        if self._thread and self._thread.is_alive():
            logger.warning(f"Camera {self.camera_id} already running.")
            return
            
        self._stop_event.clear()
        self.status = "CONNECTING"
        self._start_time = time.time()
        
        self._thread = threading.Thread(
            target=self._run_loop, 
            name=f"Worker-{self.camera_id}",
            daemon=True
        )
        self._thread.start()
        logger.info(f"Camera {self.camera_id} worker started.")

    def stop(self):
        self.status = "STOPPED"
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info(f"Camera {self.camera_id} worker stopped.")

    def update_config(self, target_fps: Optional[int] = None, buffer_size: Optional[int] = None):
        if target_fps is not None:
            self.target_fps = target_fps
            self.sampler.set_target_fps(target_fps)
        if buffer_size is not None:
            self.frame_buffer.resize(buffer_size)

    def _run_loop(self):
        retry_delay = 2.0
        max_delay = settings.MAX_RETRY_DELAY_SECONDS
        
        while not self._stop_event.is_set():
            cap = None
            try:
                self.status = "CONNECTING"
                parsed_source = parse_source(self.source_url, self.source_type)
                cap = cv2.VideoCapture(parsed_source)
                
                if not cap.isOpened():
                    raise ValueError(f"Could not open source: {parsed_source}")

                self.status = "ONLINE"
                self.last_error = None
                logger.info(f"Camera {self.camera_id} connected successfully.")
                
                # Reset retry delay on successful connection
                retry_delay = 2.0
                
                # Setup resolution
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                if width > 0 and height > 0:
                    self.resolution = f"{width}x{height}"
                
                # Read loop
                while not self._stop_event.is_set():
                    read_start = time.time()
                    ret, frame = cap.read()
                    
                    if not ret:
                        # For files, if we reach the end, we can break to restart/reconnect
                        if self.source_type == "file":
                            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            continue
                        else:
                            raise ConnectionError("Stream disconnected or frame corrupted.")

                    self.frames_received += 1
                    
                    if self.sampler.should_sample(read_start):
                        self.frames_sampled += 1
                        ts = datetime.now()
                        self.last_frame_timestamp = ts
                        
                        fd = FrameData(
                            camera_id=self.camera_id,
                            frame=frame,
                            timestamp=ts,
                            resolution=self.resolution
                        )
                        self.frame_buffer.add_frame(fd)
                        self._update_fps(read_start)
                    else:
                        self.frames_dropped += 1

            except Exception as e:
                if not self._stop_event.is_set():
                    self.status = "ERROR" if isinstance(e, ValueError) else "OFFLINE"
                    self.last_error = str(e)
                    logger.error(f"Camera {self.camera_id} error: {self.last_error}")
                    
                    # Exponential backoff for reconnections
                    self.reconnections += 1
                    self.status = "RECONNECTING"
                    logger.info(f"Camera {self.camera_id} reconnecting in {retry_delay} seconds...")
                    
                    # Wait for retry_delay unless stopped
                    start_wait = time.time()
                    while time.time() - start_wait < retry_delay and not self._stop_event.is_set():
                        time.sleep(0.5)
                        
                    retry_delay = min(retry_delay * 2, max_delay)
            finally:
                if cap is not None:
                    cap.release()

    def _update_fps(self, current_time: float):
        self._fps_window.append(current_time)
        if len(self._fps_window) > self._fps_window_size:
            self._fps_window.pop(0)
            
        if len(self._fps_window) > 1:
            time_diff = self._fps_window[-1] - self._fps_window[0]
            if time_diff > 0:
                self.current_fps = round((len(self._fps_window) - 1) / time_diff, 1)

    def get_health(self) -> dict:
        uptime = int(time.time() - self._start_time) if self._start_time > 0 else 0
        return {
            "camera_id": self.camera_id,
            "status": self.status,
            "source_type": self.source_type,
            "current_fps": self.current_fps if self.status == "ONLINE" else 0.0,
            "target_fps": self.target_fps,
            "resolution": self.resolution,
            "frames_received": self.frames_received,
            "frames_sampled": self.frames_sampled,
            "frames_dropped": self.frames_dropped,
            "reconnections": self.reconnections,
            "last_frame_timestamp": self.last_frame_timestamp,
            "last_error": self.last_error,
            "uptime_seconds": uptime if self.status != "STOPPED" else 0
        }
