import pytest
import time
from app.services.stream_manager import StreamManager

@pytest.fixture
def manager():
    mgr = StreamManager()
    yield mgr
    mgr.shutdown()

def test_stream_isolation(manager):
    # Start a valid stream and an invalid stream
    manager.start_stream("GOOD-01", "webcam", "9999", 5, 10) # 9999 is invalid but won't crash manager
    manager.start_stream("GOOD-02", "webcam", "9998", 5, 10)
    
    # Give workers a little time to start thread and fail
    time.sleep(0.5)
    
    h1 = manager.get_health("GOOD-01")
    h2 = manager.get_health("GOOD-02")
    
    assert h1["status"] in ["ERROR", "RECONNECTING", "CONNECTING"]
    assert h2["status"] in ["ERROR", "RECONNECTING", "CONNECTING"]
    
    # Even though both failed, they exist and didn't crash the manager
    assert len(manager.get_all_health()) == 2
