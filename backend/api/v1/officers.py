# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from geoalchemy2 import WKTElement
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.database import get_db
from core.limiter import limiter
from core.security import get_current_user
from models.officer import Officer
from models.road_issue import RoadIssue
from models.schemas import (
    OfficerCheckinRequest,
    OfficerCheckinResponse,
    OfficerResponse,
    RoadIssueItem,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/v1/officers', tags=['Officers'])


async def get_or_create_officer(db: AsyncSession, current_user: dict) -> Officer:
    """Helper to provision or fetch an officer profile based on login session info."""
    user_id = uuid.UUID(current_user["sub"]) if "sub" in current_user else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user identifier in token")

    stmt = select(Officer).where(Officer.id == user_id)
    officer = (await db.execute(stmt)).scalar_one_or_none()

    if not officer:
        # Auto-provision field officer profile
        email = current_user.get("email") or f"officer_{user_id.hex[:6]}@safevix.ai"
        name = current_user.get("name") or current_user.get("username") or f"Officer {user_id.hex[:6].upper()}"

        settings = get_settings()
        officer = Officer(
            id=user_id,
            name=name,
            email=email,
            role="field_officer",
            department="PWD (Roads & Bridges)",
            is_active=True,
            ward_id=settings.default_officer_ward,
        )
        db.add(officer)
        await db.commit()
        await db.refresh(officer)
        logger.info(f"Auto-provisioned officer record for {name} ({email})")

    return officer


@router.get('/me', response_model=OfficerResponse)
@limiter.limit("20/minute")
async def get_officer_profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> OfficerResponse:
    """Fetch current logged-in officer profile (auto-provisions if first login)."""
    officer = await get_or_create_officer(db, current_user)
    return OfficerResponse(
        id=officer.id,
        name=officer.name,
        phone=officer.phone,
        email=officer.email,
        role=officer.role,
        ward_id=officer.ward_id,
        department=officer.department,
        is_active=officer.is_active,
        last_checkin=officer.last_checkin,
        created_at=officer.created_at
    )


@router.post('/checkin', response_model=OfficerCheckinResponse)
@limiter.limit("15/minute")
async def officer_gps_checkin(
    request: Request,
    payload: OfficerCheckinRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> OfficerCheckinResponse:
    """Submit GPS coordinates to check-in and update officer's real-time field location."""
    officer = await get_or_create_officer(db, current_user)

    officer.last_checkin = datetime.now(UTC).replace(tzinfo=None)
    officer.last_location = WKTElement(f"POINT({payload.lon} {payload.lat})", srid=4326)

    await db.commit()
    await db.refresh(officer)

    return OfficerCheckinResponse(
        status="success",
        last_checkin=officer.last_checkin
    )


@router.get('/me/workload', response_model=list[RoadIssueItem])
@limiter.limit("20/minute")
async def get_my_workload(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> list[RoadIssueItem]:
    """Get active complaints assigned to the logged-in field officer."""
    officer = await get_or_create_officer(db, current_user)

    lat_expr = func.ST_Y(RoadIssue.location).label('lat')
    lon_expr = func.ST_X(RoadIssue.location).label('lon')

    stmt = (
        select(RoadIssue, lat_expr, lon_expr)
        .where(RoadIssue.assigned_officer_id == officer.id)
        .where(RoadIssue.status.in_(["open", "acknowledged", "in_progress"]))
        .order_by(RoadIssue.severity.desc(), RoadIssue.created_at.desc())
    )

    rows = (await db.execute(stmt)).all()

    return [
        RoadIssueItem(
            uuid=issue.uuid,
            issue_type=issue.issue_type,
            severity=issue.severity,
            description=issue.description,
            lat=float(lat),
            lon=float(lon),
            location_address=issue.location_address,
            road_name=issue.road_name,
            road_type=issue.road_type,
            road_number=issue.road_number,
            authority_name=issue.authority_name,
            status=issue.status,
            created_at=issue.created_at,
            distance_meters=0.0,
            category=issue.category,
            sub_category=issue.sub_category,
            ward_id=issue.ward_id,
            ward_name=issue.ward_name,
            assigned_officer_id=issue.assigned_officer_id,
            sla_deadline=issue.sla_deadline,
            resolved_at=issue.resolved_at,
            duplicate_of_uuid=issue.duplicate_of_uuid,
            confirmation_count=issue.confirmation_count,
            before_photo_url=issue.before_photo_url,
            after_photo_url=issue.after_photo_url
        )
        for issue, lat, lon in rows
    ]
