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
