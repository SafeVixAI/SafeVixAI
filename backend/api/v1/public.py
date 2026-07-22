# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Public Accountability API for SafeVixAI.

No-authentication transparency endpoints for public accountability:
- Ward rankings by resolution rate and response time
- Authority performance metrics
- City-wide KPIs
- Open issues map (anonymized GeoJSON)
- Public complaint status tracking
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import case, extract, func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.limiter import limiter
from models.officer import Officer
from models.road_issue import RoadIssue
from models.ward import Ward

logger = logging.getLogger("safevixai.public")

router = APIRouter(prefix='/api/v1/public', tags=['Public Accountability'])


@router.get('/ward-rankings')
@limiter.limit("30/minute")
async def get_ward_rankings(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Public ward performance rankings. Sorted by resolution rate.
    Shows: resolution rate, avg response time, total complaints, SLA breaches.
    """
    from services.ward_service import WardService
    await WardService.ensure_seeded(db)

    now = datetime.now(UTC).replace(tzinfo=None)
    active_statuses = ["open", "acknowledged", "assigned", "accepted", "in_progress"]
    resolved_statuses = ["resolved", "citizen_confirmed", "closed"]

    stmt = (
        select(
            Ward.ward_id,
            Ward.ward_name,
            Ward.zone_name,
            Ward.population,
            func.count(RoadIssue.id).label("total"),
            func.count(case((RoadIssue.status.in_(resolved_statuses), 1), else_=literal_column("NULL"))).label("resolved"),
            func.count(case((RoadIssue.status.in_(active_statuses), 1), else_=literal_column("NULL"))).label("active"),
            func.count(case(
                (
                    RoadIssue.status.in_(active_statuses) &
                    RoadIssue.sla_deadline.isnot(None) &
                    (RoadIssue.sla_deadline < now),
                    1,
                ),
                else_=literal_column("NULL"),
            )).label("breached"),
            func.avg(case(
                (
                    RoadIssue.resolved_at.isnot(None) &
                    RoadIssue.created_at.isnot(None),
                    extract('epoch', RoadIssue.resolved_at - RoadIssue.created_at) / 3600,
                ),
                else_=literal_column("NULL"),
            )).label("avg_resolution_hours"),
        )
        .outerjoin(RoadIssue, RoadIssue.ward_id == Ward.ward_id)
        .group_by(Ward.ward_id, Ward.ward_name, Ward.zone_name, Ward.population)
        .order_by(Ward.ward_name.asc())
    )

    rows = (await db.execute(stmt)).all()

    rankings = []
    for row in rows:
        total = row.total or 0
        resolved = row.resolved or 0
        resolution_rate = round((resolved / total * 100) if total > 0 else 0.0, 1)
        avg_hours = round(float(row.avg_resolution_hours), 1) if row.avg_resolution_hours else None

        rankings.append({
            "ward_id": row.ward_id,
            "ward_name": row.ward_name,
            "zone_name": row.zone_name,
            "total_complaints": total,
            "resolved": resolved,
            "active": row.active or 0,
            "sla_breached": row.breached or 0,
            "resolution_rate": resolution_rate,
            "avg_resolution_hours": avg_hours,
            "population": row.population,
        })

    rankings.sort(key=lambda x: x["resolution_rate"], reverse=True)
    for i, r in enumerate(rankings):
        r["rank"] = i + 1

    return {
        "rankings": rankings,
        "generated_at": datetime.now(UTC).isoformat(),
        "total_wards": len(rankings),
    }


@router.get('/authority-performance')
@limiter.limit("20/minute")
async def get_authority_performance(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Authority performance metrics — response times and satisfaction scores."""
    # Authority-level aggregation
    authority_stmt = (
        select(
            RoadIssue.authority_name,
            func.count(RoadIssue.id).label("total"),
            func.count(case((RoadIssue.status.in_(["resolved", "closed", "citizen_confirmed"]), 1))).label("resolved"),
        )
        .where(RoadIssue.authority_name.isnot(None))
        .group_by(RoadIssue.authority_name)
    )
    rows = (await db.execute(authority_stmt)).all()

    authorities = []
    for authority_name, total, resolved in rows:
        resolution_rate = round((resolved / total * 100) if total > 0 else 0.0, 1)
        authorities.append({
            "authority_name": authority_name,
            "total_complaints": total,
            "resolved": resolved,
            "resolution_rate": resolution_rate,
        })

    authorities.sort(key=lambda x: x["resolution_rate"], reverse=True)

    return {
        "authorities": authorities,
        "generated_at": datetime.now(UTC).isoformat(),
    }


@router.get('/stats')
@limiter.limit("60/minute")
async def get_public_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """City-wide public KPIs — total filed, resolved, avg time, categories."""
    now = datetime.now(UTC).replace(tzinfo=None)

    total = (await db.execute(select(func.count(RoadIssue.id)))).scalar() or 0
    resolved = (await db.execute(
        select(func.count(RoadIssue.id)).where(
            RoadIssue.status.in_(["resolved", "citizen_confirmed", "closed"])
        )
    )).scalar() or 0
    active = (await db.execute(
        select(func.count(RoadIssue.id)).where(
            RoadIssue.status.in_(["open", "acknowledged", "assigned", "accepted", "in_progress"])
        )
    )).scalar() or 0
    breached = (await db.execute(
        select(func.count(RoadIssue.id)).where(
            RoadIssue.status.in_(["open", "acknowledged", "assigned", "accepted", "in_progress"]),
            RoadIssue.sla_deadline.isnot(None),
            RoadIssue.sla_deadline < now,
        )
    )).scalar() or 0

    # Category breakdown
    cat_rows = (await db.execute(
        select(RoadIssue.category, func.count(RoadIssue.id))
        .group_by(RoadIssue.category)
    )).all()
    categories = {cat or "uncategorized": count for cat, count in cat_rows}

    # Severity distribution
    sev_rows = (await db.execute(
        select(RoadIssue.severity, func.count(RoadIssue.id))
        .group_by(RoadIssue.severity)
    )).all()
    severity_dist = {str(sev): count for sev, count in sev_rows}

    # Active officers
    officers_active = (await db.execute(
        select(func.count(Officer.id)).where(Officer.is_active)
    )).scalar() or 0

    resolution_rate = round((resolved / total * 100) if total > 0 else 0.0, 1)

    return {
        "total_complaints_filed": total,
        "total_resolved": resolved,
        "currently_active": active,
        "sla_breached": breached,
        "resolution_rate": resolution_rate,
        "active_field_officers": officers_active,
        "category_breakdown": categories,
        "severity_distribution": severity_dist,
        "generated_at": datetime.now(UTC).isoformat(),
        "platform": "SafeVixAI — AI-Powered Civic Intelligence",
    }


@router.get('/open-issues-map')
@limiter.limit("20/minute")
async def get_open_issues_map(
    request: Request,
    category: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Public anonymized GeoJSON map of all open issues."""
    lat_expr = func.ST_Y(RoadIssue.location).label("lat")
    lon_expr = func.ST_X(RoadIssue.location).label("lon")

    stmt = (
        select(RoadIssue, lat_expr, lon_expr)
        .where(RoadIssue.status.in_(["open", "acknowledged", "assigned", "accepted", "in_progress"]))
        .where(RoadIssue.location.isnot(None))
    )
    if category:
        stmt = stmt.where(RoadIssue.category == category)

    rows = (await db.execute(stmt)).all()

    features = []
    for issue, lat, lon in rows:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(lon), float(lat)],
            },
            "properties": {
                "complaint_ref": issue.complaint_ref,
                "category": issue.category,
                "issue_type": issue.issue_type,
                "severity": issue.severity,
                "status": issue.status,
                "ward_name": issue.ward_name,
                "days_old": _days_old(issue.created_at),
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
        "total": len(features),
        "generated_at": datetime.now(UTC).isoformat(),
    }


@router.get('/complaint/{complaint_ref}/status')
@limiter.limit("60/minute")
async def public_complaint_status(
    request: Request,
    complaint_ref: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Public complaint status check — no login needed."""
    issue = (await db.execute(
        select(RoadIssue).where(RoadIssue.complaint_ref == complaint_ref)
    )).scalar_one_or_none()

    if not issue:
        return {"found": False, "complaint_ref": complaint_ref}

    return {
        "found": True,
        "complaint_ref": issue.complaint_ref,
        "status": issue.status,
        "category": issue.category,
        "severity": issue.severity,
        "ward_name": issue.ward_name,
        "authority_name": issue.authority_name,
        "filed_days_ago": _days_old(issue.created_at),
        "resolved": issue.status in ("resolved", "citizen_confirmed", "closed"),
    }


def _days_old(created_at: datetime | None) -> int:
    if not created_at:
        return 0
    now = datetime.now(UTC).replace(tzinfo=None)
    if created_at.tzinfo:
        created_at = created_at.replace(tzinfo=None)
    return max(0, (now - created_at).days)
