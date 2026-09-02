import threading
import collections
from typing import Optional, Any
from datetime import datetime

class FrameData:
    def __init__(self, camera_id: str, frame: Any, timestamp: datetime, resolution: str):
        self.camera_id = camera_id
        self.frame = frame  # Numpy array (OpenCV image)
        self.timestamp = timestamp
        self.resolution = resolution

class FrameBuffer:
    """
    A thread-safe, bounded frame buffer.
    When maxlen is reached, old frames are dropped automatically by deque.
    """
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self._buffer = collections.deque(maxlen=max_size)
        self._lock = threading.Lock()

    def add_frame(self, frame_data: FrameData):
        with self._lock:
            self._buffer.append(frame_data)

    def get_latest_frame(self) -> Optional[FrameData]:
        with self._lock:
            if not self._buffer:
                return None
            return self._buffer[-1]
            
    def get_all_frames(self) -> list[FrameData]:
        with self._lock:
            return list(self._buffer)

    def clear(self):
        with self._lock:
            self._buffer.clear()
            
    def resize(self, new_size: int):
        with self._lock:
            if new_size != self.max_size:
                self.max_size = new_size
                new_buffer = collections.deque(self._buffer, maxlen=new_size)
                self._buffer = new_buffer
