from typing import Dict, Optional, List
from app.services.stream_worker import StreamWorker
from app.core.logging import logger

class StreamManager:
    """
    Orchestrates multiple StreamWorkers.
    Ensures failure of one stream does not impact others.
    """
    def __init__(self):
        self._workers: Dict[str, StreamWorker] = {}

    def start_stream(self, camera_id: str, source_type: str, source_url: str, target_fps: int, buffer_size: int) -> bool:
        """Starts a stream worker. Returns True if started, False if already running."""
        if camera_id in self._workers:
            worker = self._workers[camera_id]
            if worker.status not in ["STOPPED", "ERROR"]:
                return False
            # If it's stopped, we can restart it. 
            worker.update_config(target_fps=target_fps, buffer_size=buffer_size)
            worker.start()
            return True

        worker = StreamWorker(
            camera_id=camera_id,
            source_type=source_type,
            source_url=source_url,
            target_fps=target_fps,
            buffer_size=buffer_size
        )
        self._workers[camera_id] = worker
        worker.start()
        return True

    def stop_stream(self, camera_id: str) -> bool:
        """Stops a stream worker. Returns True if stopped, False if not running or not found."""
        worker = self._workers.get(camera_id)
        if not worker:
            return False
        
        if worker.status == "STOPPED":
            return False
            
        worker.stop()
        return True

    def update_stream(self, camera_id: str, target_fps: Optional[int] = None, buffer_size: Optional[int] = None):
        """Updates configuration for an active stream."""
        worker = self._workers.get(camera_id)
        if worker:
            worker.update_config(target_fps=target_fps, buffer_size=buffer_size)

    def remove_stream(self, camera_id: str):
        """Stops and removes a stream worker."""
        self.stop_stream(camera_id)
        if camera_id in self._workers:
            del self._workers[camera_id]

    def get_health(self, camera_id: str) -> Optional[dict]:
        worker = self._workers.get(camera_id)
        if not worker:
            return None
        return worker.get_health()

    def get_all_health(self) -> List[dict]:
        return [w.get_health() for w in self._workers.values()]
        
    def get_worker(self, camera_id: str) -> Optional[StreamWorker]:
        return self._workers.get(camera_id)

    def shutdown(self):
        """Stops all streams gracefully."""
        logger.info("Shutting down StreamManager...")
        for worker in self._workers.values():
            worker.stop()
        self._workers.clear()

# Singleton instance
stream_manager = StreamManager()
