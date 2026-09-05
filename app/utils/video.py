import os
import sys
from pathlib import Path
import cv2
import numpy as np
from typing import Optional, List, Any, TYPE_CHECKING

from app.core.paths import get_resource_path, get_base_dir, get_data_dir

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
    - For webcams: '0' becomes integer 0.
    - For local files: resolves relative paths against CWD, bundled resources,
      executable directory, base directory, and data directory.
    - For network streams (rtsp/http): returns string as-is.
    """
    if source_type == "webcam":
        try:
            return int(source_url)
        except ValueError:
            return source_url

    # Check if network stream
    if isinstance(source_url, str):
        url_lower = source_url.lower()
        if url_lower.startswith(("rtsp://", "http://", "https://", "rtmp://")):
            return source_url

    # File path resolution
    source_str = str(source_url)
    direct_p = Path(source_str)
    if direct_p.is_file():
        return str(direct_p.resolve())

    # Normalize relative paths (strip leading './', '.\\', '/', '\')
    clean_path = source_str.lstrip(".\\").lstrip("./").lstrip("/").lstrip("\\")

    # 1. Bundled resource directory (sys._MEIPASS in frozen mode, repo root in dev)
    res_p = get_resource_path(clean_path)
    if res_p.is_file():
        return str(res_p.resolve())

    # 2. Executable parent directory (dist/VICENTRA)
    if getattr(sys, "frozen", False):
        exe_p = Path(sys.executable).parent / clean_path
        if exe_p.is_file():
            return str(exe_p.resolve())

    # 3. Base directory (repo root)
    base_p = get_base_dir() / clean_path
    if base_p.is_file():
        return str(base_p.resolve())

    # 4. Writable user data directory (%LOCALAPPDATA%/VICENTRA)
    data_p = get_data_dir() / clean_path
    if data_p.is_file():
        return str(data_p.resolve())

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
    detections: List["Detection"] = None,
    zones: List[Any] = None,
) -> np.ndarray:
    """
    Return a *copy* of *frame* with bounding boxes, class names,
    confidence scores, and optional virtual zone overlays drawn.
    The original frame is never modified.
    """
    annotated = frame.copy()

    # 1. Draw Virtual Zone Overlays if provided
    if zones:
        for z in zones:
            # Determine color: Red (0, 0, 255) for restricted, Cyan (255, 255, 0) for monitoring
            is_restricted = getattr(z, "zone_type", "restricted") == "restricted"
            zone_color = (0, 0, 255) if is_restricted else (255, 255, 0)
            
            coords = getattr(z, "coordinates", [])
            if len(coords) >= 3:
                # Convert coords to numpy int32 array for cv2.polylines
                if isinstance(coords[0], (tuple, list)):
                    pts = np.array([[int(p[0]), int(p[1])] for p in coords], np.int32)
                elif isinstance(coords[0], dict):
                    pts = np.array([[int(p["x"]), int(p["y"])] for p in coords], np.int32)
                else:
                    pts = np.array([], np.int32)

                if len(pts) >= 3:
                    pts = pts.reshape((-1, 1, 2))

                    # Semi-transparent fill overlay
                    overlay = annotated.copy()
                    cv2.fillPoly(overlay, [pts], zone_color)
                    cv2.addWeighted(overlay, 0.15, annotated, 0.85, 0, annotated)

                    # Polygon border
                    cv2.polylines(annotated, [pts], isClosed=True, color=zone_color, thickness=2)

                    # Label at top-left vertex of polygon
                    name = getattr(z, "name", "Zone")
                    label_text = f"ZONE: {name} ({'RESTRICTED' if is_restricted else 'MONITOR'})"
                    x0, y0 = pts[0][0][0], pts[0][0][1]
                    cv2.putText(
                        annotated,
                        label_text,
                        (x0, max(20, y0 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        zone_color,
                        2,
                        cv2.LINE_AA,
                    )

    # 2. Draw Detections if provided
    if detections:
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


