import cv2
import numpy as np
from typing import Optional

def encode_frame_to_jpeg(frame: np.ndarray, quality: int = 80) -> Optional[bytes]:
    """
    Encodes a numpy array frame to JPEG format bytes.
    """
    if frame is None:
        return None
        
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    success, encoded_image = cv2.imencode('.jpg', frame, encode_param)
    
    if success:
        return encoded_image.tobytes()
    return None

def parse_source(source_url: str, source_type: str):
    """
    Converts source_url into appropriate format for OpenCV.
    For webcams, '0' needs to be integer 0.
    """
    if source_type == "webcam":
        try:
            return int(source_url)
        except ValueError:
            return source_url
    return source_url
