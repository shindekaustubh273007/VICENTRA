from sqlalchemy import Column, String, Boolean, Integer, DateTime
from sqlalchemy.sql import func
from app.database.database import Base

class Camera(Base):
    __tablename__ = "cameras"

    camera_id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)
    source_type = Column(String)  # rtsp, webcam, file
    source_url = Column(String)
    enabled = Column(Boolean, default=True)
    target_fps = Column(Integer, default=5)
    buffer_size = Column(Integer, default=10)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Zone(Base):
    __tablename__ = "zones"

    zone_id = Column(String, primary_key=True, index=True)
    camera_id = Column(String, index=True)
    name = Column(String, index=True)
    zone_type = Column(String, default="restricted")  # restricted, monitoring
    coordinates_json = Column(String)                # JSON: [{"x": 10.0, "y": 20.0}, ...]
    target_categories_json = Column(String)           # JSON: ["person", "vehicle"]
    enabled = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

