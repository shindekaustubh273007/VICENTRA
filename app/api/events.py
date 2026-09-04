"""
Phase 4 — API Endpoint for Zone & Intrusion Event retrieval.

GET /api/events — Query recent ENTER, EXIT, and INTRUSION events
"""

from typing import Optional
from fastapi import APIRouter, Query

from app.models.schemas import EventListResponse, ZoneEventSchema, PositionSchema
from app.services.event_store import event_store

router = APIRouter()


@router.get("", response_model=EventListResponse)
@router.get("/", response_model=EventListResponse, include_in_schema=False)
def get_events(
    camera_id: Optional[str] = Query(default=None, description="Filter events by camera ID"),
    zone_id: Optional[str] = Query(default=None, description="Filter events by zone ID"),
    event_type: Optional[str] = Query(
        default=None, description="Filter by event type (ENTER, EXIT, INTRUSION)"
    ),
    limit: int = Query(default=50, ge=1, le=500, description="Max events to return"),
):
    """
    Retrieve recent zone and security intrusion events.
    """
    events = event_store.get_events(
        camera_id=camera_id,
        zone_id=zone_id,
        event_type=event_type,
        limit=limit,
    )

    items = [
        ZoneEventSchema(
            event_id=e.event_id,
            event_type=e.event_type,
            camera_id=e.camera_id,
            zone_id=e.zone_id,
            zone_name=e.zone_name,
            track_id=e.track_id,
            object_class=e.object_class,
            category=e.category,
            timestamp=e.timestamp,
            position=PositionSchema(x=e.position[0], y=e.position[1]),
        )
        for e in events
    ]

    return EventListResponse(count=len(items), events=items)
