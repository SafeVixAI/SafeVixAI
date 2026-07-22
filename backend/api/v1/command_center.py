# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Command Center Enterprise API for SafeVixAI.

Real-time enterprise command center endpoints:
- SSE live complaint feed
- Officer locations
- Escalation risk board
- Spatial hotspots
- Resolution metrics
- Predictive maintenance zones
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import case, extract, func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.limiter import limiter
from core.rbac import Role, require_role
from models.officer import Officer
from models.road_issue import RoadIssue
from services.event_bus import get_event_bus

logger = logging.getLogger("safevixai.command_center")

router = APIRouter(prefix='/api/v1/command-center', tags=['Command Center'])


@router.get('/live-feed')
async def live_feed(
    request: Request,
    current_user: dict = Depends(require_role(Role.OPERATOR)),
) -> StreamingResponse:
    """
    Server-Sent Events (SSE) stream for real-time complaint updates.
    Streams domain events as they happen to the command center UI.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        bus = get_event_bus()
        queue: asyncio.Queue = asyncio.Queue()

        async def handler(event):
            await queue.put(event)

        # Subscribe to all complaint events
        bus.subscribe("*", handler)

        try:
            # Send initial connection event
            yield _sse_format("connected", {"message": "Command Center live feed connected"})

            # Send recent events as catch-up
            recent = bus.get_recent_events(limit=10)
            for event in recent:
                yield _sse_format(event.event_type, event.payload)

            # Stream new events
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield _sse_format(event.event_type, event.payload)
                except TimeoutError:
                    # Send keepalive
                    yield _sse_format("heartbeat", {"timestamp": datetime.now(UTC).isoformat()})
                except asyncio.CancelledError:
                    break
        finally:
            bus.unsubscribe("*", handler)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get('/officer-locations')
@limiter.limit("20/minute")
async def get_officer_locations(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(Role.OPERATOR)),
) -> dict:
    """Get all active field officers with their GPS positions."""
    active_statuses = ["open", "acknowledged", "assigned", "accepted", "in_progress"]
    stmt = (
        select(
            Officer,
            func.ST_Y(Officer.last_location).label("lat"),
            func.ST_X(Officer.last_location).label("lon"),
            func.count(case(
                (
                    (RoadIssue.assigned_officer_id == Officer.id) &
                    RoadIssue.status.in_(active_statuses),
                    1,
                ),
                else_=literal_column("NULL"),
            )).label("workload"),
        )
        .outerjoin(RoadIssue, RoadIssue.assigned_officer_id == Officer.id)
        .where(Officer.is_active)
        .group_by(Officer.id)
    )
    rows = (await db.execute(stmt)).all()

    locations = []
    for o, lat, lon, workload in rows:
        locations.append({
            "officer_id": str(o.id),
            "name": o.name,
            "department": o.department,
            "ward_id": o.ward_id,
            "lat": float(lat) if lat else None,
            "lon": float(lon) if lon else None,
            "last_checkin": o.last_checkin.isoformat() if o.last_checkin else None,
            "current_workload": workload or 0,
            "is_active": o.is_active,
        })

    return {
        "officers": locations,
        "total": len(locations),
        "generated_at": datetime.now(UTC).isoformat(),
    }


@router.get('/escalation-board')
@limiter.limit("15/minute")
async def get_escalation_board(
    request: Request,
    min_risk: float = Query(default=0.25, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(Role.OPERATOR)),
) -> dict:
    """Escalation risk board — complaints sorted by predicted escalation risk."""
    from services.escalation_predictor import EscalationPredictor

    predictions = await EscalationPredictor.batch_predict(db, min_risk=min_risk)

    return {
        "escalation_risks": [
            {
                "issue_uuid": p.issue_uuid,
                "risk_score": p.risk_score,
                "risk_level": p.risk_level,
                "contributing_factors": p.contributing_factors,
                "recommended_action": p.recommended_action,
                "predicted_escalation_hours": p.predicted_escalation_hours,
            }
            for p in predictions
        ],
        "total": len(predictions),
        "critical_count": sum(1 for p in predictions if p.risk_level == "critical"),
        "high_count": sum(1 for p in predictions if p.risk_level == "high"),
        "generated_at": datetime.now(UTC).isoformat(),
    }


@router.get('/hotspots')
@limiter.limit("15/minute")
async def get_hotspots(
    request: Request,
    eps_meters: float = Query(default=200, ge=50, le=2000),
    min_samples: int = Query(default=3, ge=2, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(Role.OPERATOR)),
) -> dict:
    """Spatial complaint clusters (hotspots) using DBSCAN."""
    from services.complaint_cluster import dbscan_cluster

    # Fetch active complaints with coordinates
    lat_expr = func.ST_Y(RoadIssue.location).label("lat")
    lon_expr = func.ST_X(RoadIssue.location).label("lon")

    stmt = (
        select(RoadIssue, lat_expr, lon_expr)
        .where(RoadIssue.status.in_(["open", "acknowledged", "assigned", "accepted", "in_progress"]))
        .where(RoadIssue.location.isnot(None))
    )
    rows = (await db.execute(stmt)).all()

    points = [
        {
            "uuid": str(issue.uuid),
            "lat": float(lat),
            "lon": float(lon),
            "issue_type": issue.issue_type or "unknown",
            "severity": issue.severity or 3,
        }
        for issue, lat, lon in rows
    ]

    clusters = dbscan_cluster(points, eps_meters=eps_meters, min_samples=min_samples)

    return {
        "hotspots": [
            {
                "cluster_id": c.cluster_id,
                "centroid": {"lat": c.centroid_lat, "lon": c.centroid_lon},
                "complaint_count": c.point_count,
                "radius_meters": round(c.radius_meters, 1),
                "dominant_issue_type": c.dominant_issue_type,
                "avg_severity": round(c.avg_severity, 1),
                "issue_types": c.issue_types,
            }
            for c in clusters
        ],
        "total_hotspots": len(clusters),
        "total_complaints_analyzed": len(points),
        "generated_at": datetime.now(UTC).isoformat(),
    }


@router.get('/resolution-metrics')
@limiter.limit("15/minute")
async def get_resolution_metrics(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(Role.OPERATOR)),
) -> dict:
    """Resolution metrics broken down by ward, category, and severity."""
    resolved_statuses = ["resolved", "citizen_confirmed", "closed"]

    # By category — single aggregate query
    cat_stmt = (
        select(
            RoadIssue.category,
            func.count(RoadIssue.id).label("total"),
            func.count(case(
                (RoadIssue.status.in_(resolved_statuses), 1),
                else_=literal_column("NULL"),
            )).label("resolved"),
            func.avg(case(
                (RoadIssue.resolved_at.isnot(None), extract('epoch', RoadIssue.resolved_at - RoadIssue.created_at) / 3600),
                else_=literal_column("NULL"),
            )).label("avg_hours"),
        )
        .where(RoadIssue.category.in_(["roads", "traffic", "streetlight"]))
        .group_by(RoadIssue.category)
    )
    cat_rows = (await db.execute(cat_stmt)).all()
    cat_lookup = {r.category: r for r in cat_rows}

    cat_metrics = []
    for category in ["roads", "traffic", "streetlight"]:
        r = cat_lookup.get(category)
        total = r.total if r else 0
        resolved = r.resolved if r else 0
        avg_hours = round(float(r.avg_hours), 1) if r and r.avg_hours else None
        cat_metrics.append({
            "category": category,
            "total": total,
            "resolved": resolved,
            "resolution_rate": round((resolved / total * 100) if total > 0 else 0.0, 1),
            "avg_resolution_hours": avg_hours,
        })

    # By severity — single aggregate query
    sev_stmt = (
        select(
            RoadIssue.severity,
            func.count(RoadIssue.id).label("total"),
            func.count(case(
                (RoadIssue.status.in_(resolved_statuses), 1),
                else_=literal_column("NULL"),
            )).label("resolved"),
        )
        .where(RoadIssue.severity.between(1, 5))
        .group_by(RoadIssue.severity)
        .order_by(RoadIssue.severity.asc())
    )
    sev_rows = (await db.execute(sev_stmt)).all()
    sev_lookup = {r.severity: r for r in sev_rows}

    sev_metrics = []
    for sev in range(1, 6):
        r = sev_lookup.get(sev)
        total = r.total if r else 0
        resolved = r.resolved if r else 0
        sev_metrics.append({
            "severity": sev,
            "total": total,
            "resolved": resolved,
            "resolution_rate": round((resolved / total * 100) if total > 0 else 0.0, 1),
        })

    return {
        "by_category": cat_metrics,
        "by_severity": sev_metrics,
        "generated_at": datetime.now(UTC).isoformat(),
    }


@router.get('/event-bus-health')
@limiter.limit("10/minute")
async def event_bus_health(
    request: Request,
    current_user: dict = Depends(require_role(Role.OPERATOR)),
) -> dict:
    """Event bus operational health metrics."""
    bus = get_event_bus()
    return {
        "metrics": bus.get_metrics(),
        "dead_letters": bus.get_dead_letters(limit=5),
        "generated_at": datetime.now(UTC).isoformat(),
    }


def _sse_format(event_type: str, data: dict) -> str:
    """Format data as SSE event string."""
    return f"event: {event_type}\ndata: {json.dumps(data, default=str)}\n\n"
