import cv2
import numpy as np
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.detector import Detection

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


# ─── Phase 2: Annotation ────────────────────────────────────────────

# Colour palette per category (BGR)
_COLOURS = {
    "person": (0, 200, 0),      # green
    "vehicle": (255, 160, 0),   # blue-ish orange (BGR)
}
_DEFAULT_COLOUR = (0, 255, 255)  # yellow


def annotate_frame(
    frame: np.ndarray,
    detections: List["Detection"],
) -> np.ndarray:
    """
    Return a *copy* of *frame* with bounding boxes, class names,
    and confidence scores drawn for each detection.
    The original frame is never modified.
    """
    annotated = frame.copy()

    for det in detections:
        colour = _COLOURS.get(det.category, _DEFAULT_COLOUR)
        x1, y1 = int(det.bounding_box.x1), int(det.bounding_box.y1)
        x2, y2 = int(det.bounding_box.x2), int(det.bounding_box.y2)

        # Bounding box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), colour, 2)

        # Label text
        label = f"{det.class_name} {det.confidence:.2f}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        (tw, th), baseline = cv2.getTextSize(label, font, font_scale, thickness)

        # Background rectangle for text readability
        cv2.rectangle(
            annotated,
            (x1, y1 - th - baseline - 4),
            (x1 + tw + 4, y1),
            colour,
            cv2.FILLED,
        )
        cv2.putText(
            annotated,
            label,
            (x1 + 2, y1 - baseline - 2),
            font,
            font_scale,
            (0, 0, 0),
            thickness,
            cv2.LINE_AA,
        )

    return annotated

