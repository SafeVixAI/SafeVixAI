# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Field Workflow API for SafeVixAI.

Mobile-first endpoints for field officers in the field:
- Start work (GPS + timestamp verified)
- Upload before/after evidence
- Complete resolution with geo-verification
- GPS check-in with proximity validation
- Get optimized route
"""

from __future__ import annotations

import logging
import math
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.limiter import limiter
from core.rbac import Role, require_role
from models.road_issue import RoadIssue
from services.complaint_state_machine import ComplaintStateMachine, InvalidTransitionError

logger = logging.getLogger("safevixai.field_workflow")

router = APIRouter(prefix='/api/v1/field', tags=['Field Workflow'])

GEO_VERIFY_RADIUS_METERS = 200  # Officer must be within 200m of complaint


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class StartWorkRequest(BaseModel):
    officer_lat: float = Field(..., description="Officer's current GPS latitude")
    officer_lon: float = Field(..., description="Officer's current GPS longitude")
    notes: str | None = None


class CompleteWorkRequest(BaseModel):
    officer_lat: float
    officer_lon: float
    resolution_notes: str = Field(..., min_length=5, description="What was done to resolve")
    after_photo_url: str | None = None  # Could also be uploaded via /upload-evidence


class GeoCheckinRequest(BaseModel):
    lat: float
    lon: float


class EvidenceUploadResponse(BaseModel):
    status: str
    evidence_type: str
    saved: bool


@router.post('/complaints/{issue_uuid}/start-work')
@limiter.limit("20/minute")
async def start_field_work(
    request: Request,
    issue_uuid: str,
    body: StartWorkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(Role.FIELD_OFFICER)),
) -> dict:
    """Officer marks field work started. GPS is recorded and verified against complaint location."""
    try:
        cid = uuid.UUID(issue_uuid)
        actor_id = uuid.UUID(current_user["sub"]) if "sub" in current_user else None
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Fetch issue to verify GPS proximity
    issue = (await db.execute(
        select(RoadIssue).where(RoadIssue.uuid == cid)
    )).scalar_one_or_none()

    if not issue:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Get complaint coordinates
    complaint_lat, complaint_lon = await _get_issue_coords(db, issue)
    geo_verified = False
    distance_m = None

    if complaint_lat and complaint_lon:
        distance_m = _haversine_meters(body.officer_lat, body.officer_lon, complaint_lat, complaint_lon)
        geo_verified = distance_m <= GEO_VERIFY_RADIUS_METERS

    try:
        result = await ComplaintStateMachine.transition(
            db,
            complaint_uuid=cid,
            target_status="in_progress",
            actor_id=actor_id,
            actor_role="field_officer",
            notes=body.notes or "Field work commenced",
            metadata={
                "officer_gps": {"lat": body.officer_lat, "lon": body.officer_lon},
                "geo_verified": geo_verified,
                "distance_meters": round(distance_m, 1) if distance_m else None,
            },
        )
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return {
        "status": "work_started",
        "complaint_ref": result.issue.complaint_ref if result.issue else None,
        "geo_verified": geo_verified,
        "distance_meters": round(distance_m, 1) if distance_m else None,
        "work_started_at": datetime.now(UTC).isoformat(),
    }


@router.post('/complaints/{issue_uuid}/complete')
@limiter.limit("15/minute")
async def complete_field_work(
    request: Request,
    issue_uuid: str,
    body: CompleteWorkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(Role.FIELD_OFFICER)),
) -> dict:
    """Officer marks complaint as resolved with GPS verification and evidence."""
    try:
        cid = uuid.UUID(issue_uuid)
        actor_id = uuid.UUID(current_user["sub"]) if "sub" in current_user else None
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    issue = (await db.execute(
        select(RoadIssue).where(RoadIssue.uuid == cid)
    )).scalar_one_or_none()

    if not issue:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # GPS verification
    complaint_lat, complaint_lon = await _get_issue_coords(db, issue)
    geo_verified = False
    distance_m = None

    if complaint_lat and complaint_lon:
        distance_m = _haversine_meters(body.officer_lat, body.officer_lon, complaint_lat, complaint_lon)
        geo_verified = distance_m <= GEO_VERIFY_RADIUS_METERS

    # Save after photo if provided
    if body.after_photo_url:
        issue.after_photo_url = body.after_photo_url

    try:
        result = await ComplaintStateMachine.transition(
            db,
            complaint_uuid=cid,
            target_status="resolved",
            actor_id=actor_id,
            actor_role="field_officer",
            notes=body.resolution_notes,
            metadata={
                "resolution_gps": {"lat": body.officer_lat, "lon": body.officer_lon},
                "geo_verified": geo_verified,
                "distance_meters": round(distance_m, 1) if distance_m else None,
                "has_after_photo": bool(body.after_photo_url),
            },
        )
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return {
        "status": "resolved",
        "complaint_ref": result.issue.complaint_ref if result.issue else None,
        "geo_verified": geo_verified,
        "resolved_at": datetime.now(UTC).isoformat(),
        "resolution_notes": body.resolution_notes,
    }


@router.post('/complaints/{issue_uuid}/geo-checkin')
@limiter.limit("30/minute")
async def geo_checkin_at_complaint(
    request: Request,
    issue_uuid: str,
    body: GeoCheckinRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(Role.FIELD_OFFICER)),
) -> dict:
    """Verify officer is physically at the complaint location."""
    try:
        cid = uuid.UUID(issue_uuid)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid UUID")

    issue = (await db.execute(
        select(RoadIssue).where(RoadIssue.uuid == cid)
    )).scalar_one_or_none()

    if not issue:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint_lat, complaint_lon = await _get_issue_coords(db, issue)

    if not complaint_lat or not complaint_lon:
        return {"verified": False, "reason": "Complaint has no GPS coordinates"}

    distance_m = _haversine_meters(body.lat, body.lon, complaint_lat, complaint_lon)
    verified = distance_m <= GEO_VERIFY_RADIUS_METERS

    return {
        "verified": verified,
        "distance_meters": round(distance_m, 1),
        "max_radius_meters": GEO_VERIFY_RADIUS_METERS,
        "complaint_location": {"lat": complaint_lat, "lon": complaint_lon},
    }


@router.get('/my-route')
@limiter.limit("10/minute")
async def get_optimized_route(
    request: Request,
    lat: float,
    lon: float,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(Role.FIELD_OFFICER)),
) -> dict:
    """Get optimized complaint visit route from officer's current position."""
    try:
        officer_id = current_user["sub"]
    except KeyError:
        raise HTTPException(status_code=401, detail="Invalid token")

    from services.officer_route_optimizer import OfficerRouteOptimizer

    route = await OfficerRouteOptimizer.optimize_route(
        db,
        officer_id=officer_id,
        officer_lat=lat,
        officer_lon=lon,
    )

    return {
        "officer_id": route.officer_id,
        "total_stops": route.total_stops,
        "total_distance_km": route.total_distance_km,
        "estimated_duration_minutes": route.estimated_duration_minutes,
        "warnings": route.warnings,
        "stops": [
            {
                "order": s.order,
                "complaint_ref": s.complaint_ref,
                "issue_type": s.issue_type,
                "severity": s.severity,
                "lat": s.lat,
                "lon": s.lon,
                "distance_from_prev_km": s.distance_from_prev_km,
                "estimated_arrival_minutes": s.estimated_arrival_minutes,
                "address": s.address,
            }
            for s in route.stops
        ],
    }


async def _get_issue_coords(db: AsyncSession, issue: RoadIssue) -> tuple[float | None, float | None]:
    """Extract lat/lon from a RoadIssue's PostGIS location."""
    if not issue.location:
        return None, None
    try:
        lat_expr = func.ST_Y(RoadIssue.location).label("lat")
        lon_expr = func.ST_X(RoadIssue.location).label("lon")
        row = (await db.execute(
            select(lat_expr, lon_expr).where(RoadIssue.uuid == issue.uuid)
        )).first()
        if row:
            return float(row[0]), float(row[1])
    except Exception:
        logger.debug("Field workflow — location coords unavailable for issue %s", issue.uuid)
    return None, None
