# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.audit import AuditLog
from core.database import get_db
from core.limiter import limiter
from core.rbac import Role, require_role
from models.officer import Officer
from models.road_issue import RoadIssue
from models.schemas import OfficerResponse, RoadIssueItem, RoadIssuesResponse
from services.complaint_lifecycle import ComplaintLifecycle

router = APIRouter(prefix='/api/v1/admin', tags=['Admin Operations'])


@router.get('/complaints', response_model=RoadIssuesResponse)
@limiter.limit("20/minute")
async def get_all_complaints_admin(
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None),
    category: str | None = Query(default=None),
    ward_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(Role.OPERATOR))
) -> RoadIssuesResponse:
    """Administrator lists, searches, and filters all complaints with pagination."""
    lat_expr = func.ST_Y(RoadIssue.location).label('lat')
    lon_expr = func.ST_X(RoadIssue.location).label('lon')

    base_stmt = select(RoadIssue)

    if status:
        base_stmt = base_stmt.where(RoadIssue.status == status)
    if category:
        base_stmt = base_stmt.where(RoadIssue.category == category)
    if ward_id:
        base_stmt = base_stmt.where(RoadIssue.ward_id == ward_id)

    # Get total count
    count_stmt = select(func.count(RoadIssue.id))
    if status:
        count_stmt = count_stmt.where(RoadIssue.status == status)
    if category:
        count_stmt = count_stmt.where(RoadIssue.category == category)
    if ward_id:
        count_stmt = count_stmt.where(RoadIssue.ward_id == ward_id)

    total_count = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        base_stmt.add_columns(lat_expr, lon_expr)
        .order_by(RoadIssue.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    rows = (await db.execute(stmt)).all()
    issues = [
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

    next_offset = offset + limit if (offset + limit) < total_count else None
    return RoadIssuesResponse(
        issues=issues,
        count=len(issues),
        radius_used=0,
        next_offset=next_offset,
        total_count=total_count
    )


@router.post('/complaints/{issue_uuid}/assign', response_model=dict)
@limiter.limit("15/minute")
async def assign_complaint_to_officer(
    request: Request,
    issue_uuid: str,
    officer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(Role.OPERATOR))
) -> dict:
    """Manually assign a complaint to an officer (starts SLA tracking)."""
    try:
        complaint_uuid = uuid.UUID(issue_uuid)
        off_uuid = uuid.UUID(officer_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid UUID format") from exc

    actor_id = uuid.UUID(current_user["sub"]) if "sub" in current_user else None

    try:
        issue = await ComplaintLifecycle.assign_officer(
            db=db,
            complaint_uuid=complaint_uuid,
            officer_id=off_uuid,
            actor_id=actor_id,
            actor_role="operator"
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    ip = request.client.host if request.client else "unknown"
    AuditLog.log_admin_action(
        str(current_user.get("sub", "unknown")),
        "complaint_assigned",
        ip,
        {"complaint_ref": issue.complaint_ref, "officer_id": officer_id}
    )
    return {
        "status": "assigned",
        "complaint_ref": issue.complaint_ref,
        "assigned_officer_id": str(issue.assigned_officer_id),
        "sla_deadline": issue.sla_deadline.isoformat() if issue.sla_deadline else None
    }


@router.get('/officers', response_model=list[OfficerResponse])
@limiter.limit("20/minute")
async def list_officers_admin(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(Role.OPERATOR))
) -> list[OfficerResponse]:
    """List all registered civic officers and active field teams."""
    stmt = select(Officer).order_by(Officer.name.asc())
    result = await db.execute(stmt)
    officers = result.scalars().all()

    return [
        OfficerResponse(
            id=o.id,
            name=o.name,
            phone=o.phone,
            email=o.email,
            role=o.role,
            ward_id=o.ward_id,
            department=o.department,
            is_active=o.is_active,
            last_checkin=o.last_checkin,
            created_at=o.created_at
        )
        for o in officers
    ]


@router.get('/dashboard', response_model=dict)
@limiter.limit("20/minute")
async def get_dashboard_summary_admin(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(Role.OPERATOR))
) -> dict:
    """Retrieve high-level smart city dashboard overall KPI summaries."""
    # 1. Total active open/acknowledged/in_progress
    active_stmt = select(func.count(RoadIssue.id)).where(RoadIssue.status.in_(["open", "acknowledged", "in_progress"]))
    active_count = (await db.execute(active_stmt)).scalar() or 0

    # 2. Resolved
    resolved_stmt = select(func.count(RoadIssue.id)).where(RoadIssue.status == "resolved")
    resolved_count = (await db.execute(resolved_stmt)).scalar() or 0

    # 3. Total
    total_stmt = select(func.count(RoadIssue.id))
    total_count = (await db.execute(total_stmt)).scalar() or 0

    # 4. SLA breaches
    now = datetime.now(UTC).replace(tzinfo=None)
    breached_stmt = select(func.count(RoadIssue.id)).where(
        RoadIssue.status.in_(["open", "acknowledged", "in_progress"]),
        RoadIssue.sla_deadline.is_not(None),
        RoadIssue.sla_deadline < now
    )
    breached_count = (await db.execute(breached_stmt)).scalar() or 0

    # 5. Category breakdown
    cat_stmt = select(RoadIssue.category, func.count(RoadIssue.id)).group_by(RoadIssue.category)
    cat_rows = (await db.execute(cat_stmt)).all()
    categories = {"roads": 0, "traffic": 0, "streetlight": 0}
    for cat, count in cat_rows:
        if cat in categories:
            categories[cat] = count

    # 6. Officers count
    off_stmt = select(func.count(Officer.id))
    officers_count = (await db.execute(off_stmt)).scalar() or 0

    return {
        "kpis": {
            "active_complaints": active_count,
            "resolved_complaints": resolved_count,
            "total_complaints": total_count,
            "sla_breaches": breached_count,
            "active_field_officers": officers_count,
            "overall_resolution_rate": round((resolved_count / total_count * 100.0) if total_count > 0 else 0.0, 1)
        },
        "category_breakdown": categories
    }


@router.post('/cleanup-expired-data', response_model=dict)
@limiter.limit("1/minute")
async def trigger_data_retention_cleanup(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(Role.OPERATOR))
) -> dict:
    """
    Trigger database cleanup of expired data.
    Removes old chat logs (>90 days), SOS incidents (>90 days), and live tracking sessions (>30 days).
    """
    try:
        # Call the cleanup function defined in migrations
        await db.execute("SELECT safevixai_cleanup_expired_data()")
        await db.commit()

        ip = request.client.host if request.client else "unknown"
        AuditLog.log_admin_action(
            str(current_user.get("sub", "unknown")),
            "data_retention_cleanup",
            ip
        )
        return {
            "status": "success",
            "message": "Data retention cleanup executed successfully",
            "function": "safevixai_cleanup_expired_data()",
            "cleanup_policies": {
                "live_tracking": "30 days inactive",
                "chat_logs": "90 days old",
                "sos_incidents": "90 days old"
            }
        }
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Data cleanup failed: {str(exc)}"
        ) from exc


@router.get('/cache/status', response_model=dict)
@limiter.limit("10/minute")
async def get_cache_status_admin(
    request: Request,
    current_user: dict = Depends(require_role(Role.OPERATOR))
) -> dict:
    """Retrieve current Redis caching infrastructure status and memory metrics."""
    from core.config import get_settings
    from core.redis_client import create_cache
    settings = get_settings()
    cache = create_cache(settings.redis_url)
    status = {"status": "online" if cache._client else "fallback_in_memory"}
    await cache.close()
    return status


@router.post('/cache/purge', response_model=dict)
@limiter.limit("5/minute")
async def purge_cache_admin(
    request: Request,
    key_prefix: str | None = Query(default=None, description="Prefix to purge or empty for all"),
    current_user: dict = Depends(require_role(Role.OPERATOR))
) -> dict:
    """Purge specific cache prefixes or flush entire Redis cache database."""
    from core.config import get_settings
    from core.redis_client import create_cache
    settings = get_settings()
    cache = create_cache(settings.redis_url)
    if cache._client:
        if key_prefix:
            keys = await cache._client.keys(f"{key_prefix}*")
            if keys:
                await cache._client.delete(*keys)
        else:
            await cache._client.flushdb()
    await cache.close()
    ip = request.client.host if request.client else "unknown"
    AuditLog.log_admin_action(
        str(current_user.get("sub", "unknown")),
        "cache_purge",
        ip,
        {"key_prefix": key_prefix or "all"}
    )
    return {"status": "success", "message": f"Purged cache prefix: {key_prefix or 'ALL'}"}
