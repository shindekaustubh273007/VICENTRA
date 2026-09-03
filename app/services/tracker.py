import math
import uuid
from typing import List, Dict, Optional
from datetime import datetime

from app.core.config import settings
from app.services.detector import Detection, BoundingBox

class TrackedObject:
    def __init__(self, track_id: str, camera_id: str, initial_detection: Detection):
        self.track_id = track_id
        self.camera_id = camera_id
        
        self.class_id = initial_detection.class_id
        self.class_name = initial_detection.class_name
        self.category = initial_detection.category
        
        self.current_bounding_box = initial_detection.bounding_box
        self.current_position = self._get_centroid(initial_detection.bounding_box)
        self.confidence = initial_detection.confidence
        
        self.first_seen = initial_detection.timestamp
        self.last_seen = initial_detection.timestamp
        
        self.position_history: List[tuple[float, float]] = [self.current_position]
        self.missed_frames = 0
        self.track_age = 1
        
    def _get_centroid(self, box: BoundingBox) -> tuple[float, float]:
        cx = (box.x1 + box.x2) / 2.0
        cy = (box.y1 + box.y2) / 2.0
        return (cx, cy)
        
    def update(self, detection: Detection):
        self.current_bounding_box = detection.bounding_box
        self.current_position = self._get_centroid(detection.bounding_box)
        self.confidence = detection.confidence
        self.last_seen = detection.timestamp
        self.missed_frames = 0
        self.track_age += 1
        
        self.position_history.append(self.current_position)
        if len(self.position_history) > settings.TRACKING_MAX_HISTORY:
            self.position_history.pop(0)

    def predict_missed(self):
        """Called when no detection matches this object in the current frame."""
        self.missed_frames += 1
        self.track_age += 1
        
    def is_expired(self) -> bool:
        return self.missed_frames > settings.TRACKING_MAX_MISSED_FRAMES
        
    def to_dict(self) -> dict:
        return {
            "track_id": self.track_id,
            "camera_id": self.camera_id,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "category": self.category,
            "confidence": round(self.confidence, 4),
            "current_bounding_box": self.current_bounding_box.to_dict(),
            "current_position": {"x": self.current_position[0], "y": self.current_position[1]},
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "track_age": self.track_age,
            "missed_frames": self.missed_frames,
            "position_history": [{"x": p[0], "y": p[1]} for p in self.position_history]
        }

class ObjectTracker:
    """
    Per-camera object tracker using simple centroid distance.
    Associates Detection objects to TrackedObjects across frames.
    """
    def __init__(self, camera_id: str):
        self.camera_id = camera_id
        self.tracks: Dict[str, TrackedObject] = {}
        self.association_threshold = settings.TRACKING_ASSOCIATION_THRESHOLD
        
    def _distance(self, p1: tuple[float, float], p2: tuple[float, float]) -> float:
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
        
    def _get_centroid(self, box: BoundingBox) -> tuple[float, float]:
        return ((box.x1 + box.x2) / 2.0, (box.y1 + box.y2) / 2.0)

    def update(self, detections: List[Detection]) -> List[TrackedObject]:
        """
        Takes detections from a new frame, associates them with existing tracks,
        creates new tracks, and prunes expired tracks.
        """
        unmatched_detections = list(detections)
        unmatched_tracks = set(self.tracks.keys())
        
        matches = []
        for det in unmatched_detections[:]:
            det_centroid = self._get_centroid(det.bounding_box)
            best_dist = float('inf')
            best_track_id = None
            
            for track_id in unmatched_tracks:
                track = self.tracks[track_id]
                if track.class_id != det.class_id:
                    continue
                    
                dist = self._distance(det_centroid, track.current_position)
                if dist < best_dist and dist < self.association_threshold:
                    best_dist = dist
                    best_track_id = track_id
                    
            if best_track_id is not None:
                matches.append((best_track_id, det))
                unmatched_detections.remove(det)
                unmatched_tracks.remove(best_track_id)
                
        # Update matched tracks
        for track_id, det in matches:
            self.tracks[track_id].update(det)
            
        # Update unmatched tracks (missed)
        expired_tracks = []
        for track_id in unmatched_tracks:
            track = self.tracks[track_id]
            track.predict_missed()
            if track.is_expired():
                expired_tracks.append(track_id)
                
        # Remove expired tracks
        for track_id in expired_tracks:
            del self.tracks[track_id]
            
        # Create new tracks for unmatched detections
        for det in unmatched_detections:
            new_track_id = str(uuid.uuid4())[:8]  # Short UUID for MVP
            self.tracks[new_track_id] = TrackedObject(new_track_id, self.camera_id, det)
            
        return list(self.tracks.values())
