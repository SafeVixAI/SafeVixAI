# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import case, func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.limiter import limiter
from models.road_issue import RoadIssue
from models.schemas import (
    AnalyticsHeatmapResponse,
    HeatmapFeature,
    HeatmapFeatureGeometry,
    HeatmapFeatureProperties,
    RoadIssueItem,
    WardSummaryItem,
)
from models.ward import Ward
from services.ward_service import WardService

router = APIRouter(prefix='/api/v1/analytics', tags=['Analytics'])


@router.get('/heatmap', response_model=AnalyticsHeatmapResponse)
@limiter.limit("20/minute")
async def get_heatmap_geojson(
    request: Request,
    category: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db)
) -> AnalyticsHeatmapResponse:
    """Get active complaints as a GeoJSON FeatureCollection for rendering choropleth maps/heatmaps."""
    lat_expr = func.ST_Y(RoadIssue.location).label('lat')
    lon_expr = func.ST_X(RoadIssue.location).label('lon')

    stmt = (
        select(RoadIssue, lat_expr, lon_expr)
        .where(RoadIssue.status.in_(["open", "acknowledged", "in_progress"]))
    )
    if category:
        stmt = stmt.where(RoadIssue.category == category)

    rows = (await db.execute(stmt)).all()

    features = []
    for issue, lat, lon in rows:
        features.append(
            HeatmapFeature(
                geometry=HeatmapFeatureGeometry(coordinates=[float(lon), float(lat)]),
                properties=HeatmapFeatureProperties(
                    uuid=issue.uuid,
                    category=issue.category or "roads",
                    severity=issue.severity,
                    status=issue.status
                )
            )
        )

    return AnalyticsHeatmapResponse(features=features)


@router.get('/ward-summary', response_model=list[WardSummaryItem])
@limiter.limit("20/minute")
async def get_ward_summary(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> list[WardSummaryItem]:
    """Get complaint metrics, resolution rates, and SLA breaches grouped by ward."""
    await WardService.ensure_seeded(db)

    now = datetime.now(UTC).replace(tzinfo=None)
    active_statuses = ["open", "acknowledged", "in_progress"]

    stmt = (
        select(
            Ward.ward_id,
            Ward.ward_name,
            Ward.zone_name,
            func.count(case(
                (RoadIssue.status.in_(active_statuses), 1),
                else_=literal_column("NULL"),
            )).label("open_count"),
            func.count(case(
                (RoadIssue.status == "resolved", 1),
                else_=literal_column("NULL"),
            )).label("resolved_count"),
            func.count(case(
                (RoadIssue.status == "rejected", 1),
                else_=literal_column("NULL"),
            )).label("rejected_count"),
            func.count(case(
                (
                    RoadIssue.status.in_(active_statuses) &
                    RoadIssue.sla_deadline.is_not(None) &
                    (RoadIssue.sla_deadline < now),
                    1,
                ),
                else_=literal_column("NULL"),
            )).label("breached_count"),
        )
        .outerjoin(RoadIssue, RoadIssue.ward_id == Ward.ward_id)
        .group_by(Ward.ward_id, Ward.ward_name, Ward.zone_name)
        .order_by(Ward.ward_name.asc())
    )

    rows = (await db.execute(stmt)).all()

    summary = []
    for row in rows:
        total = (row.open_count or 0) + (row.resolved_count or 0) + (row.rejected_count or 0)
        resolution_rate = (row.resolved_count / total * 100.0) if total > 0 else 0.0

        summary.append(
            WardSummaryItem(
                ward_id=row.ward_id,
                ward_name=row.ward_name,
                zone_name=row.zone_name,
                open_issues=row.open_count or 0,
                resolved_issues=row.resolved_count or 0,
                resolution_rate=round(resolution_rate, 2),
                sla_breach_count=row.breached_count or 0,
            )
        )

    return summary


@router.get('/sla-breach', response_model=list[RoadIssueItem])
@limiter.limit("20/minute")
async def get_sla_breaches(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> list[RoadIssueItem]:
    """Get unresolved complaints that have breached their SLA timeline."""
    now = datetime.now(UTC).replace(tzinfo=None)
    lat_expr = func.ST_Y(RoadIssue.location).label('lat')
    lon_expr = func.ST_X(RoadIssue.location).label('lon')

    stmt = (
        select(RoadIssue, lat_expr, lon_expr)
        .where(RoadIssue.status.in_(["open", "acknowledged", "in_progress"]))
        .where(RoadIssue.sla_deadline.is_not(None))
        .where(RoadIssue.sla_deadline < now)
        .order_by(RoadIssue.sla_deadline.asc())
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


@router.get('/category-breakdown', response_model=dict[str, int])
@limiter.limit("20/minute")
async def get_category_breakdown(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> dict[str, int]:
    """Get active complaints breakdown by top-level category."""
    stmt = (
        select(RoadIssue.category, func.count(RoadIssue.id))
        .where(RoadIssue.status.in_(["open", "acknowledged", "in_progress"]))
        .group_by(RoadIssue.category)
    )
    result = await db.execute(stmt)
    rows = result.all()

    breakdown = {"roads": 0, "traffic": 0, "streetlight": 0}
    for cat, count in rows:
        if cat in breakdown:
            breakdown[cat] = count

    return breakdown
