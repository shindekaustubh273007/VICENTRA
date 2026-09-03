import pytest
from datetime import datetime, timedelta
from app.services.detector import Detection, BoundingBox
from app.services.tracker import ObjectTracker, TrackedObject
from app.core.config import settings

def create_detection(x1, y1, x2, y2, class_id=0, class_name="person", category="person", conf=0.9):
    ts = datetime.utcnow()
    return Detection(
        camera_id="cam-1",
        timestamp=ts,
        frame_timestamp=ts.isoformat(),
        class_id=class_id,
        class_name=class_name,
        category=category,
        confidence=conf,
        bounding_box=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2)
    )

def test_tracker_creates_new_track():
    tracker = ObjectTracker("cam-1")
    det = create_detection(100, 100, 200, 200)
    tracks = tracker.update([det])
    
    assert len(tracks) == 1
    assert tracks[0].class_name == "person"
    assert tracks[0].track_age == 1
    assert tracks[0].missed_frames == 0
    assert len(tracks[0].position_history) == 1
    
def test_tracker_associates_same_object():
    tracker = ObjectTracker("cam-1")
    
    # Frame 1
    det1 = create_detection(100, 100, 200, 200)
    tracks1 = tracker.update([det1])
    assert len(tracks1) == 1
    track_id = tracks1[0].track_id
    
    # Frame 2 (Object moved slightly)
    det2 = create_detection(105, 105, 205, 205)
    tracks2 = tracker.update([det2])
    
    assert len(tracks2) == 1
    assert tracks2[0].track_id == track_id  # Should have same ID
    assert tracks2[0].track_age == 2
    assert len(tracks2[0].position_history) == 2

def test_tracker_handles_missed_frames():
    tracker = ObjectTracker("cam-1")
    settings.TRACKING_MAX_MISSED_FRAMES = 2
    
    # Frame 1
    det = create_detection(100, 100, 200, 200)
    tracker.update([det])
    track_id = list(tracker.tracks.keys())[0]
    
    # Frame 2 (Missed)
    tracker.update([])
    assert track_id in tracker.tracks
    assert tracker.tracks[track_id].missed_frames == 1
    
    # Frame 3 (Missed)
    tracker.update([])
    assert track_id in tracker.tracks
    assert tracker.tracks[track_id].missed_frames == 2
    
    # Frame 4 (Missed - Should Expire)
    tracker.update([])
    assert track_id not in tracker.tracks

def test_tracker_differentiates_objects():
    tracker = ObjectTracker("cam-1")
    
    # Frame 1: Two distant objects
    det1 = create_detection(10, 10, 20, 20)
    det2 = create_detection(300, 300, 350, 350)
    
    tracks = tracker.update([det1, det2])
    assert len(tracks) == 2
    assert tracks[0].track_id != tracks[1].track_id
