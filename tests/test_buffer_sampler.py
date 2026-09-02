import pytest
from datetime import datetime
from app.services.frame_buffer import FrameBuffer, FrameData
from app.services.frame_sampler import FrameSampler
import time

def test_frame_buffer_limits():
    buffer = FrameBuffer(max_size=3)
    for i in range(5):
        fd = FrameData("cam", i, datetime.now(), "1080")
        buffer.add_frame(fd)
        
    frames = buffer.get_all_frames()
    assert len(frames) == 3
    # Should contain the last 3 items: 2, 3, 4
    assert frames[0].frame == 2
    assert frames[-1].frame == 4
    
def test_frame_sampler():
    sampler = FrameSampler(target_fps=2)
    # interval is 0.5 sec
    
    assert sampler.should_sample(current_time=1.0) == True
    assert sampler.should_sample(current_time=1.2) == False
    assert sampler.should_sample(current_time=1.5) == True
