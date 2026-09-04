import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.database import Base, get_db
from app.services.stream_manager import stream_manager

from sqlalchemy.pool import StaticPool

SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup():
    # Setup
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    stream_manager.shutdown()
    yield
    # Teardown
    stream_manager.shutdown()

def test_create_camera():
    response = client.post(
        "/api/cameras/",
        json={
            "camera_id": "TEST-01",
            "name": "Test Camera",
            "location": "Loc",
            "source_type": "file",
            "source_url": "dummy.mp4",
            "target_fps": 5,
            "buffer_size": 10
        }
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["camera_id"] == "TEST-01"

def test_get_camera():
    client.post(
        "/api/cameras/",
        json={"camera_id": "TEST-02", "name": "Cam2", "location": "L", "source_type": "webcam", "source_url": "0"}
    )
    res = client.get("/api/cameras/TEST-02")
    assert res.status_code == 200
    assert res.json()["name"] == "Cam2"

def test_invalid_camera_config():
    response = client.post(
        "/api/cameras/",
        json={
            "camera_id": "TEST-03",
            "name": "Test Camera",
            "location": "Loc",
            "source_type": "invalid_type",
            "source_url": "dummy.mp4"
        }
    )
    assert response.status_code == 422 # Pydantic validation error

def test_start_stop_stream():
    client.post(
        "/api/cameras/",
        json={"camera_id": "TEST-04", "name": "Cam4", "location": "L", "source_type": "file", "source_url": "dummy.mp4", "enabled": False}
    )
    
    # Enable first to allow start. This auto-starts the stream.
    client.put("/api/cameras/TEST-04", json={"enabled": True})
    
    # Test start already running
    res = client.post("/api/cameras/TEST-04/start")
    assert res.status_code == 400
    
    # Test stop
    res = client.post("/api/cameras/TEST-04/stop")
    assert res.status_code == 200
    
    # Test stop already stopped
    res = client.post("/api/cameras/TEST-04/stop")
    assert res.status_code == 400
    
    # Test start again
    res = client.post("/api/cameras/TEST-04/start")
    assert res.status_code == 200
