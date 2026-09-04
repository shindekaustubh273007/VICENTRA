"""
Phase 4 — Geometry utilities for zone evaluation.

Implements Ray-Casting algorithm for point-in-polygon checks and
position evaluation from bounding boxes.
"""

from typing import List, Tuple, Union, Dict, Any
from app.services.detector import BoundingBox


def point_in_polygon(
    point: Tuple[float, float],
    polygon: List[Tuple[float, float]],
) -> bool:
    """
    Determines if point (x, y) is inside polygon using the Ray-Casting algorithm.

    * point: (x, y) tuple
    * polygon: list of (x, y) tuples representing polygon vertices in order
    """
    if len(polygon) < 3:
        return False

    x, y = point
    n = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    else:
                        xinters = p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def get_evaluation_point(
    box: Union[BoundingBox, Dict[str, float]],
    mode: str = "bottom_center",
) -> Tuple[float, float]:
    """
    Computes the reference point of an object bounding box for zone checking.

    Default mode 'bottom_center' is ideal for objects/people on ground planes.
    """
    if isinstance(box, BoundingBox):
        x1, y1, x2, y2 = box.x1, box.y1, box.x2, box.y2
    elif isinstance(box, dict):
        x1, y1, x2, y2 = box["x1"], box["y1"], box["x2"], box["y2"]
    else:
        raise ValueError("Invalid bounding box object")

    cx = (x1 + x2) / 2.0
    if mode == "bottom_center":
        return (cx, float(y2))
    elif mode == "centroid":
        return (cx, (y1 + y2) / 2.0)
    else:
        return (cx, float(y2))
