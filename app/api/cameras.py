from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.database import models
from app.models import schemas
from app.services.stream_manager import stream_manager
from app.services.provider import provider
from app.utils.video import encode_frame_to_jpeg

router = APIRouter()

@router.get("", response_model=List[schemas.CameraResponse])
def get_cameras(db: Session = Depends(get_db)):
    cameras = db.query(models.Camera).all()
    return cameras

@router.post("", response_model=schemas.CameraResponse, status_code=status.HTTP_201_CREATED)
def create_camera(camera: schemas.CameraCreate, db: Session = Depends(get_db)):
    db_camera = db.query(models.Camera).filter(models.Camera.camera_id == camera.camera_id).first()
    if db_camera:
        raise HTTPException(status_code=400, detail="Camera ID already registered")
    
    new_camera = models.Camera(**camera.model_dump())
    db.add(new_camera)
    db.commit()
    db.refresh(new_camera)
    
    # Auto-start if enabled
    if new_camera.enabled:
        stream_manager.start_stream(
            camera_id=new_camera.camera_id,
            source_type=new_camera.source_type,
            source_url=new_camera.source_url,
            target_fps=new_camera.target_fps,
            buffer_size=new_camera.buffer_size
        )
        
    return new_camera

@router.get("/{camera_id}", response_model=schemas.CameraResponse)
def get_camera(camera_id: str, db: Session = Depends(get_db)):
    camera = db.query(models.Camera).filter(models.Camera.camera_id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera

@router.put("/{camera_id}", response_model=schemas.CameraResponse)
def update_camera(camera_id: str, camera_update: schemas.CameraUpdate, db: Session = Depends(get_db)):
    db_camera = db.query(models.Camera).filter(models.Camera.camera_id == camera_id).first()
    if not db_camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    update_data = camera_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_camera, key, value)
        
    db.commit()
    db.refresh(db_camera)
    
    # Update running stream config
    stream_manager.update_stream(
        camera_id=camera_id,
        target_fps=db_camera.target_fps,
        buffer_size=db_camera.buffer_size
    )
    
    if "enabled" in update_data:
        if db_camera.enabled:
            stream_manager.start_stream(
                camera_id=db_camera.camera_id,
                source_type=db_camera.source_type,
                source_url=db_camera.source_url,
                target_fps=db_camera.target_fps,
                buffer_size=db_camera.buffer_size
            )
        else:
            stream_manager.stop_stream(camera_id)
            
    return db_camera

@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_camera(camera_id: str, db: Session = Depends(get_db)):
    db_camera = db.query(models.Camera).filter(models.Camera.camera_id == camera_id).first()
    if not db_camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    stream_manager.remove_stream(camera_id)
    db.delete(db_camera)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/{camera_id}/start")
def start_camera_stream(camera_id: str, db: Session = Depends(get_db)):
    db_camera = db.query(models.Camera).filter(models.Camera.camera_id == camera_id).first()
    if not db_camera:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    if not db_camera.enabled:
        raise HTTPException(status_code=400, detail="Cannot start a disabled camera. Enable it first.")
        
    started = stream_manager.start_stream(
        camera_id=db_camera.camera_id,
        source_type=db_camera.source_type,
        source_url=db_camera.source_url,
        target_fps=db_camera.target_fps,
        buffer_size=db_camera.buffer_size
    )
    
    if not started:
        raise HTTPException(status_code=400, detail="Stream already running or cannot be started.")
    return {"message": f"Stream started for camera {camera_id}"}

@router.post("/{camera_id}/stop")
def stop_camera_stream(camera_id: str, db: Session = Depends(get_db)):
    db_camera = db.query(models.Camera).filter(models.Camera.camera_id == camera_id).first()
    if not db_camera:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    stopped = stream_manager.stop_stream(camera_id)
    if not stopped:
        raise HTTPException(status_code=400, detail="Stream is not running.")
    return {"message": f"Stream stopped for camera {camera_id}"}

@router.get("/{camera_id}/status")
@router.get("/{camera_id}/health", response_model=schemas.StreamHealth)
def get_camera_health(camera_id: str):
    health = stream_manager.get_health(camera_id)
    if not health:
        raise HTTPException(status_code=404, detail="Camera health not found (Stream worker not initialized)")
    return health

@router.get("/{camera_id}/frame", response_class=Response)
def get_camera_frame(camera_id: str):
    frame_data = provider.get_latest_frame(camera_id)
    if not frame_data or frame_data.frame is None:
        raise HTTPException(status_code=404, detail="No frame available for this camera yet.")
        
    encoded_frame = encode_frame_to_jpeg(frame_data.frame)
    if not encoded_frame:
        raise HTTPException(status_code=500, detail="Failed to encode frame")
        
    return Response(content=encoded_frame, media_type="image/jpeg")
