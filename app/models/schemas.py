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


# ─── Phase 2: AI Detection Schemas ──────────────────────────────────

class BoundingBoxSchema(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

class DetectionSchema(BaseModel):
    camera_id: str
    timestamp: datetime
    frame_timestamp: str
    class_id: int
    class_name: str
    category: str
    confidence: float
    bounding_box: BoundingBoxSchema

class DetectionListResponse(BaseModel):
    camera_id: str
    count: int
    detections: list[DetectionSchema]

class InferenceCameraStatus(BaseModel):
    camera_id: str
    status: str
    frames_processed: int = 0
    frames_skipped: int = 0
    total_detections: int = 0
    average_inference_ms: float = 0.0
    inference_fps: float = 0.0
    detections_per_class: dict = {}

class InferenceStatusResponse(BaseModel):
    ai_enabled: bool = True
    model_name: Optional[str] = None
    selected_device: Optional[str] = None
    confidence_threshold: Optional[float] = None
    iou_threshold: Optional[float] = None
    cameras: list[InferenceCameraStatus] = []

