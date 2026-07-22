# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Officer route optimization service.

Provides nearest-neighbor TSP route optimization for field officers
to efficiently visit assigned complaints with shift-aware scheduling.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.road_issue import RoadIssue

logger = logging.getLogger(__name__)


@dataclass
class OfficerShift:
    """Shift configuration for a field officer."""
    start_time: time = field(default_factory=lambda: time(9, 0))   # 09:00
    end_time: time = field(default_factory=lambda: time(18, 0))     # 18:00
    max_complaints_per_shift: int = 12
    avg_minutes_per_stop: int = 20  # time spent at each complaint


@dataclass
class RouteStop:
    """A stop on the optimized officer route."""
    order: int
    complaint_ref: str
    issue_type: str
    severity: int
    lat: float
    lon: float
    distance_from_prev_km: float
    estimated_arrival_minutes: int
    ward_id: str | None = None
    address: str | None = None


@dataclass
class OptimizedRoute:
    """Result of route optimization."""
    officer_id: str
    total_stops: int
    total_distance_km: float
    estimated_duration_minutes: int
    stops: list[RouteStop]
    shift: OfficerShift
    warnings: list[str] = field(default_factory=list)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in kilometers."""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _nearest_neighbor_tsp(
    points: list[dict[str, Any]],
    start_lat: float,
    start_lon: float,
) -> list[dict[str, Any]]:
    """
    Nearest-neighbor heuristic TSP solver.
    
    Greedy algorithm that always visits the nearest unvisited point.
    O(n²) but fast enough for officer routes (typically < 20 stops).
    """
    if not points:
        return []

    remaining = list(range(len(points)))
    route_order = []
    current_lat, current_lon = start_lat, start_lon

    while remaining:
        best_idx = -1
        best_dist = float('inf')

        for idx in remaining:
            p = points[idx]
            d = _haversine_km(current_lat, current_lon, p['lat'], p['lon'])
            # Priority bonus: high severity complaints get distance discount
            severity_bonus = max(0, (p.get('severity', 3) - 3)) * 0.5
            adjusted_d = max(0.01, d - severity_bonus)
            if adjusted_d < best_dist:
                best_dist = adjusted_d
                best_idx = idx

        if best_idx >= 0:
            route_order.append(best_idx)
            remaining.remove(best_idx)
            current_lat = points[best_idx]['lat']
            current_lon = points[best_idx]['lon']

    return [points[i] for i in route_order]


class OfficerRouteOptimizer:
    """Optimizes field officer routes for complaint visits."""

    @staticmethod
    async def optimize_route(
        db: AsyncSession,
        *,
        officer_id: str,
        officer_lat: float,
        officer_lon: float,
        city: str | None = None,
        ward_id: str | None = None,
        shift: OfficerShift | None = None,
    ) -> OptimizedRoute:
        """
        Generate an optimized route for an officer starting from their current location.
        
        Prioritizes by: severity (descending) then SLA deadline (ascending).
        Then applies nearest-neighbor TSP for route order.
        """
        if shift is None:
            shift = OfficerShift()

        # Fetch assigned/open complaints
        stmt = (
            select(RoadIssue)
            .where(RoadIssue.status.in_(["open", "acknowledged", "in_progress"]))
            .where(RoadIssue.location.isnot(None))
            .order_by(RoadIssue.severity.desc(), RoadIssue.created_at.asc())
            .limit(shift.max_complaints_per_shift * 2)  # fetch extra for filtering
        )

        if city:
            stmt = stmt.where(RoadIssue.city == city)
        if ward_id:
            stmt = stmt.where(RoadIssue.ward_id == ward_id)

        result = await db.execute(stmt)
        issues = result.scalars().all()

        if not issues:
            return OptimizedRoute(
                officer_id=officer_id,
                total_stops=0,
                total_distance_km=0,
                estimated_duration_minutes=0,
                stops=[],
                shift=shift,
                warnings=["No open complaints found"],
            )

        # Build point list
        points = []
        for issue in issues:
            try:
                lat = issue.latitude or (func.ST_Y(issue.location) if issue.location else None)
                lon = issue.longitude or (func.ST_X(issue.location) if issue.location else None)

                # Fallback: use issue's stored coordinates
                if hasattr(issue, 'latitude') and issue.latitude:
                    lat = issue.latitude
                    lon = issue.longitude
                else:
                    continue  # skip if no coordinates

                points.append({
                    'complaint_ref': issue.complaint_ref,
                    'issue_type': issue.issue_type or 'unknown',
                    'severity': issue.severity or 3,
                    'lat': float(lat),
                    'lon': float(lon),
                    'ward_id': getattr(issue, 'ward_id', None),
                    'address': getattr(issue, 'address', None),
                })
            except (TypeError, ValueError):
                continue

        # Cap to shift max
        points = points[:shift.max_complaints_per_shift]

        # Optimize route order
        ordered = _nearest_neighbor_tsp(points, officer_lat, officer_lon)

        # Build route stops
        stops: list[RouteStop] = []
        prev_lat, prev_lon = officer_lat, officer_lon
        cumulative_minutes = 0
        total_distance = 0.0
        warnings: list[str] = []

        for idx, p in enumerate(ordered):
            dist = _haversine_km(prev_lat, prev_lon, p['lat'], p['lon'])
            # Estimate travel time: avg 25 km/h in Indian city traffic
            travel_minutes = int(dist / 25 * 60)
            cumulative_minutes += travel_minutes + shift.avg_minutes_per_stop
            total_distance += dist

            stops.append(RouteStop(
                order=idx + 1,
                complaint_ref=p['complaint_ref'],
                issue_type=p['issue_type'],
                severity=p['severity'],
                lat=p['lat'],
                lon=p['lon'],
                distance_from_prev_km=round(dist, 2),
                estimated_arrival_minutes=cumulative_minutes,
                ward_id=p.get('ward_id'),
                address=p.get('address'),
            ))

            prev_lat, prev_lon = p['lat'], p['lon']

        # Shift boundary check
        shift_hours = (
            datetime.combine(datetime.today(), shift.end_time)
            - datetime.combine(datetime.today(), shift.start_time)
        ).seconds / 3600
        shift_minutes = int(shift_hours * 60)

        if cumulative_minutes > shift_minutes:
            over = cumulative_minutes - shift_minutes
            warnings.append(
                f"Route exceeds shift by ~{over} minutes. "
                f"Consider reducing to {len(stops) - 1} stops."
            )

        return OptimizedRoute(
            officer_id=officer_id,
            total_stops=len(stops),
            total_distance_km=round(total_distance, 2),
            estimated_duration_minutes=cumulative_minutes,
            stops=stops,
            shift=shift,
            warnings=warnings,
        )
