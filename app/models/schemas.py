from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Literal
from datetime import datetime
import re

class CameraBase(BaseModel):
    name: str
    location: str
    source_type: Literal["rtsp", "webcam", "file"]
    source_url: str
    enabled: bool = True
    target_fps: int = Field(default=5, ge=1, le=120)
    buffer_size: int = Field(default=10, ge=1, le=100)

class CameraCreate(CameraBase):
    camera_id: str

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    source_type: Optional[Literal["rtsp", "webcam", "file"]] = None
    source_url: Optional[str] = None
    enabled: Optional[bool] = None
    target_fps: Optional[int] = Field(default=None, ge=1, le=120)
    buffer_size: Optional[int] = Field(default=None, ge=1, le=100)

class CameraResponse(CameraBase):
    camera_id: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        # Mask credentials in RTSP URL
        if data.get('source_type') == 'rtsp' and data.get('source_url'):
            url = data['source_url']
            # Match rtsp://user:pass@host:port/path
            masked_url = re.sub(r'(rtsp://[^:]+:)[^@]+(@)', r'\1****\2', url)
            data['source_url'] = masked_url
        return data
        
class StreamHealth(BaseModel):
    camera_id: str
    status: Literal["DISABLED", "CONNECTING", "ONLINE", "RECONNECTING", "OFFLINE", "ERROR", "STOPPED"]
    source_type: str
    current_fps: float
    target_fps: int
    resolution: Optional[str] = "--"
    frames_received: int
    frames_sampled: int
    frames_dropped: int
    reconnections: int
    last_frame_timestamp: Optional[datetime] = None
    last_error: Optional[str] = None
    uptime_seconds: int
