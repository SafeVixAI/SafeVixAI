# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Workload Balancer for SafeVixAI.

Intelligent officer assignment that considers:
1. Current workload (open complaints assigned)
2. Ward assignment (prefer ward-specific officers)
3. Shift awareness (is officer on-shift now?)
4. Historical resolution speed (performance score)
5. Geo proximity (distance from last checkin to complaint)
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import datetime, time, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.officer import Officer
from models.road_issue import RoadIssue

logger = logging.getLogger("safevixai.workload_balancer")


@dataclass
class OfficerScore:
    """Scored officer candidate for assignment."""
    officer_id: str
    officer_name: str
    department: str
    ward_id: str | None
    current_workload: int
    is_on_shift: bool
    distance_km: float | None
    composite_score: float   # Higher = better candidate
    reasons: list[str]


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class WorkloadBalancer:
    """Selects the optimal officer for complaint assignment."""

    # Shift hours (IST: 09:00 - 18:00)
    SHIFT_START = time(9, 0)
    SHIFT_END = time(18, 0)
    MAX_WORKLOAD = 15  # Max open complaints per officer

    @classmethod
    async def find_best_officer(
        cls,
        db: AsyncSession,
        *,
        complaint_lat: float,
        complaint_lon: float,
        ward_id: str | None = None,
        department: str | None = None,
        severity: int = 3,
    ) -> OfficerScore | None:
        """Find the best available officer for a complaint."""
        candidates = await cls._score_candidates(
            db,
            complaint_lat=complaint_lat,
            complaint_lon=complaint_lon,
            ward_id=ward_id,
            department=department,
            severity=severity,
        )

        if not candidates:
            logger.warning("No available officers found for ward=%s, dept=%s", ward_id, department)
            return None

        # Return highest scored officer
        best = candidates[0]
        logger.info(
            "Best officer: %s (score=%.2f, workload=%d, reasons=%s)",
            best.officer_name, best.composite_score, best.current_workload, best.reasons,
        )
        return best

    @classmethod
    async def _score_candidates(
        cls,
        db: AsyncSession,
        *,
        complaint_lat: float,
        complaint_lon: float,
        ward_id: str | None,
        department: str | None,
        severity: int,
    ) -> list[OfficerScore]:
        """Score all available officers and rank them."""
        # Fetch active officers
        stmt = select(Officer).where(Officer.is_active)
        if department:
            stmt = stmt.where(Officer.department == department)
        
        officers = (await db.execute(stmt)).scalars().all()

        if not officers:
            return []

        # Get workload counts
        workload_stmt = (
            select(RoadIssue.assigned_officer_id, func.count(RoadIssue.id))
            .where(RoadIssue.status.in_(["open", "acknowledged", "assigned", "accepted", "in_progress"]))
            .where(RoadIssue.assigned_officer_id.isnot(None))
            .group_by(RoadIssue.assigned_officer_id)
        )
        workload_rows = (await db.execute(workload_stmt)).all()
        workload_map = {str(oid): count for oid, count in workload_rows}

        now = datetime.now(timezone.utc)
        current_time = now.time()
        is_shift_time = cls.SHIFT_START <= current_time <= cls.SHIFT_END

        scored: list[OfficerScore] = []

        for officer in officers:
            oid = str(officer.id)
            workload = workload_map.get(oid, 0)
            reasons = []
            score = 100.0  # Start with base score

            # Skip overloaded officers
            if workload >= cls.MAX_WORKLOAD:
                continue

            # Factor 1: Workload (lower is better) — 30% weight
            workload_score = max(0, 1.0 - (workload / cls.MAX_WORKLOAD))
            score += workload_score * 30
            if workload == 0:
                reasons.append("No current workload")
            elif workload < 5:
                reasons.append(f"Light workload ({workload})")

            # Factor 2: Ward match — 25% weight
            if ward_id and officer.ward_id == ward_id:
                score += 25
                reasons.append("Ward officer match")

            # Factor 3: Shift awareness — 15% weight
            on_shift = is_shift_time
            if officer.last_checkin:
                # Consider recently checked-in as on-shift
                checkin = officer.last_checkin
                if checkin.tzinfo is None:
                    from datetime import timezone as tz
                    checkin = checkin.replace(tzinfo=tz.utc)
                hours_since = (now - checkin).total_seconds() / 3600
                if hours_since < 1:
                    on_shift = True
                    score += 15
                    reasons.append("Recently checked in")
                elif hours_since < 4 and is_shift_time:
                    score += 10
                    reasons.append("Active within shift window")
            elif is_shift_time:
                score += 5  # Assume on-shift during business hours

            # Factor 4: Geo proximity — 20% weight
            distance_km = None
            if officer.last_location:
                try:
                    from geoalchemy2.shape import to_shape
                    point = to_shape(officer.last_location)
                    distance_km = _haversine_km(
                        complaint_lat, complaint_lon,
                        point.y, point.x,
                    )
                    # Closer is better (within 10km gets full score)
                    proximity_score = max(0, 1.0 - (distance_km / 10.0))
                    score += proximity_score * 20
                    if distance_km < 2:
                        reasons.append(f"Very close ({distance_km:.1f}km)")
                    elif distance_km < 5:
                        reasons.append(f"Nearby ({distance_km:.1f}km)")
                except Exception:
                    logger.debug("Workload balancer — proximity score failed for officer")

            # Factor 5: Severity urgency — 10% weight
            if severity >= 4 and workload < 3:
                score += 10
                reasons.append("Available for urgent assignment")

            if not reasons:
                reasons.append("General availability")

            scored.append(OfficerScore(
                officer_id=oid,
                officer_name=officer.name,
                department=officer.department or "Unknown",
                ward_id=officer.ward_id,
                current_workload=workload,
                is_on_shift=on_shift,
                distance_km=round(distance_km, 2) if distance_km else None,
                composite_score=round(score, 2),
                reasons=reasons,
            ))

        # Sort by composite score descending
        scored.sort(key=lambda x: x.composite_score, reverse=True)
        return scored
