"""
Phase 4 — API Endpoints for Virtual Zone Management.

POST /api/cameras/{camera_id}/zones — Create virtual zone
GET /api/cameras/{camera_id}/zones  — List zones for camera
GET /api/zones/{zone_id}             — Get zone details
PUT /api/zones/{zone_id}             — Update zone
DELETE /api/zones/{zone_id}          — Delete zone
"""

import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database import models
from app.models import schemas
from app.services.zone_store import zone_store, ZoneData

camera_zone_router = APIRouter()
zone_router = APIRouter()


# ─── Camera-Scoped Zone Endpoints ────────────────────────────────────

@camera_zone_router.post(
    "/{camera_id}/zones",
    response_model=schemas.ZoneResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_camera_zone(
    camera_id: str,
    zone: schemas.ZoneCreate,
    db: Session = Depends(get_db),
):
    # Verify camera exists
    db_cam = db.query(models.Camera).filter(models.Camera.camera_id == camera_id).first()
    if not db_cam:
        raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found")

    zone_id = zone.zone_id or str(uuid.uuid4())[:8]
    existing = db.query(models.Zone).filter(models.Zone.zone_id == zone_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Zone ID '{zone_id}' already registered")

    coords_list = [(p.x, p.y) for p in zone.coordinates]
    coords_json = json.dumps([{"x": p.x, "y": p.y} for p in zone.coordinates])
    cats_json = json.dumps(zone.target_categories)

    db_zone = models.Zone(
        zone_id=zone_id,
        camera_id=camera_id,
        name=zone.name,
        zone_type=zone.zone_type,
        coordinates_json=coords_json,
        target_categories_json=cats_json,
        enabled=zone.enabled,
    )
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)

    # Sync into zone_store
    zone_data = ZoneData(
        zone_id=db_zone.zone_id,
        camera_id=camera_id,
        name=db_zone.name,
        zone_type=db_zone.zone_type,
        coordinates=coords_list,
        target_categories=zone.target_categories,
        enabled=db_zone.enabled,
        created_at=db_zone.created_at,
        updated_at=db_zone.updated_at,
    )
    zone_store.set_zone(zone_data)

    return schemas.ZoneResponse(
        zone_id=db_zone.zone_id,
        camera_id=camera_id,
        name=db_zone.name,
        zone_type=db_zone.zone_type,
        coordinates=zone.coordinates,
        target_categories=zone.target_categories,
        enabled=db_zone.enabled,
        created_at=db_zone.created_at,
        updated_at=db_zone.updated_at,
    )


@camera_zone_router.get(
    "/{camera_id}/zones",
    response_model=schemas.ZoneListResponse,
)
def list_camera_zones(camera_id: str, db: Session = Depends(get_db)):
    db_zones = db.query(models.Zone).filter(models.Zone.camera_id == camera_id).all()

    zones_out = []
    for z in db_zones:
        coords_raw = json.loads(z.coordinates_json) if z.coordinates_json else []
        coords_schema = [schemas.PositionSchema(x=p["x"], y=p["y"]) for p in coords_raw]
        cats = json.loads(z.target_categories_json) if z.target_categories_json else ["all"]

        zones_out.append(
            schemas.ZoneResponse(
                zone_id=z.zone_id,
                camera_id=z.camera_id,
                name=z.name,
                zone_type=z.zone_type,
                coordinates=coords_schema,
                target_categories=cats,
                enabled=z.enabled,
                created_at=z.created_at,
                updated_at=z.updated_at,
            )
        )

    return schemas.ZoneListResponse(
        camera_id=camera_id,
        count=len(zones_out),
        zones=zones_out,
    )


# ─── Direct Zone Endpoints ───────────────────────────────────────────

@zone_router.get("/{zone_id}", response_model=schemas.ZoneResponse)
def get_zone(zone_id: str, db: Session = Depends(get_db)):
    z = db.query(models.Zone).filter(models.Zone.zone_id == zone_id).first()
    if not z:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found")

    coords_raw = json.loads(z.coordinates_json) if z.coordinates_json else []
    coords_schema = [schemas.PositionSchema(x=p["x"], y=p["y"]) for p in coords_raw]
    cats = json.loads(z.target_categories_json) if z.target_categories_json else ["all"]

    return schemas.ZoneResponse(
        zone_id=z.zone_id,
        camera_id=z.camera_id,
        name=z.name,
        zone_type=z.zone_type,
        coordinates=coords_schema,
        target_categories=cats,
        enabled=z.enabled,
        created_at=z.created_at,
        updated_at=z.updated_at,
    )


@zone_router.put("/{zone_id}", response_model=schemas.ZoneResponse)
def update_zone(
    zone_id: str,
    zone_update: schemas.ZoneUpdate,
    db: Session = Depends(get_db),
):
    z = db.query(models.Zone).filter(models.Zone.zone_id == zone_id).first()
    if not z:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found")

    update_data = zone_update.model_dump(exclude_unset=True)

    if "name" in update_data:
        z.name = update_data["name"]
    if "zone_type" in update_data:
        z.zone_type = update_data["zone_type"]
    if "enabled" in update_data:
        z.enabled = update_data["enabled"]
    if "coordinates" in update_data and update_data["coordinates"]:
        coords_models = update_data["coordinates"]
        z.coordinates_json = json.dumps([{"x": p.x, "y": p.y} for p in coords_models])
    if "target_categories" in update_data and update_data["target_categories"]:
        z.target_categories_json = json.dumps(update_data["target_categories"])

    db.commit()
    db.refresh(z)

    # Sync memory store
    coords_raw = json.loads(z.coordinates_json)
    coords_tuples = [(float(p["x"]), float(p["y"])) for p in coords_raw]
    coords_schema = [schemas.PositionSchema(x=p["x"], y=p["y"]) for p in coords_raw]
    cats = json.loads(z.target_categories_json) if z.target_categories_json else ["all"]

    zone_data = ZoneData(
        zone_id=z.zone_id,
        camera_id=z.camera_id,
        name=z.name,
        zone_type=z.zone_type,
        coordinates=coords_tuples,
        target_categories=cats,
        enabled=z.enabled,
        created_at=z.created_at,
        updated_at=z.updated_at,
    )
    zone_store.set_zone(zone_data)

    return schemas.ZoneResponse(
        zone_id=z.zone_id,
        camera_id=z.camera_id,
        name=z.name,
        zone_type=z.zone_type,
        coordinates=coords_schema,
        target_categories=cats,
        enabled=z.enabled,
        created_at=z.created_at,
        updated_at=z.updated_at,
    )


@zone_router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zone(zone_id: str, db: Session = Depends(get_db)):
    z = db.query(models.Zone).filter(models.Zone.zone_id == zone_id).first()
    if not z:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found")

    zone_store.remove_zone(zone_id)
    db.delete(z)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
