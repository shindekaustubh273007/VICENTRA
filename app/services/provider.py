from typing import Optional, Any, Dict
from app.services.stream_manager import stream_manager
from app.services.frame_buffer import FrameData

class FrameProvider:
    """
    Clean interface for future AI modules to consume frames without
    needing to know about RTSP, OpenCV, or threading.
    """
    def __init__(self):
        self._manager = stream_manager

    def get_latest_frame(self, camera_id: str) -> Optional[FrameData]:
        """Returns the most recent FrameData from the buffer."""
        worker = self._manager.get_worker(camera_id)
        if not worker:
            return None
        return worker.frame_buffer.get_latest_frame()

    def get_sampled_frame(self, camera_id: str) -> Optional[FrameData]:
        """Same as get_latest_frame for MVP. Future extensions can add more specific logic."""
        return self.get_latest_frame(camera_id)

    def get_frame_metadata(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """Returns metadata about the stream and latest frame without image bytes."""
        fd = self.get_latest_frame(camera_id)
        health = self._manager.get_health(camera_id)
        
        if not health:
            return None
            
        return {
            "camera_id": camera_id,
            "timestamp": fd.timestamp.isoformat() if fd else None,
            "resolution": health.get("resolution"),
            "status": health.get("status"),
            "current_fps": health.get("current_fps")
        }

provider = FrameProvider()
