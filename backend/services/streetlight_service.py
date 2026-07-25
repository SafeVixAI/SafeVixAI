# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Streetlight asset management service.

QR code pole lookup, asset registry CRUD, outage tracking,
and simple predictive maintenance scoring.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.streetlight_pole import StreetlightPole

logger = logging.getLogger(__name__)


def generate_pole_qr(city: str, ward_id: str, sequence: int) -> str:
    """Generate a deterministic QR code string for a pole.

    Format: SVAI-{CITY_CODE}-{WARD}-{SEQ:04d}
    Example: SVAI-CHN-W050-0001
    """
    city_code = city[:3].upper()
    ward_code = (ward_id or 'X').replace('ward_', 'W').upper()[:4]
    return f"SVAI-{city_code}-{ward_code}-{sequence:04d}"


class StreetlightService:
    """Service for streetlight pole asset management."""

    @staticmethod
    async def lookup_by_qr(db: AsyncSession, qr_code: str) -> StreetlightPole | None:
        """Find a pole by its QR code (citizen scan flow)."""
        stmt = select(StreetlightPole).where(StreetlightPole.qr_code == qr_code)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def lookup_by_pole_id(db: AsyncSession, pole_id: str) -> StreetlightPole | None:
        """Find a pole by its unique pole_id."""
        stmt = select(StreetlightPole).where(StreetlightPole.pole_id == pole_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def find_nearby(
        db: AsyncSession,
        lat: float,
        lon: float,
        radius_meters: int = 500,
        limit: int = 50,
    ) -> list[StreetlightPole]:
        """Find streetlight poles within radius of a coordinate."""
        point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        point_geo = cast(point, Geography)
        pole_geo = cast(StreetlightPole.location, Geography)

        stmt = (
            select(StreetlightPole)
            .where(StreetlightPole.location.isnot(None))
            .where(func.ST_DWithin(pole_geo, point_geo, radius_meters))
            .order_by(func.ST_Distance(pole_geo, point_geo))
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def report_outage(
        db: AsyncSession,
        pole_id: str,
        reporter_notes: str | None = None,
    ) -> StreetlightPole | None:
        """Mark a pole as non-operational (outage reported)."""
        stmt = select(StreetlightPole).where(StreetlightPole.pole_id == pole_id)
        result = await db.execute(stmt)
        pole = result.scalar_one_or_none()

        if pole:
            pole.is_operational = False
            pole.failure_count += 1
            pole.last_failure_at = datetime.now(UTC)

            # Append to maintenance history
            history = pole.maintenance_history or []
            history.append({
                'date': datetime.now(UTC).isoformat(),
                'type': 'outage_reported',
                'notes': reporter_notes or 'Citizen reported via QR scan',
            })
            pole.maintenance_history = history

            await db.commit()
            await db.refresh(pole)
            logger.info("Outage reported for pole %s (failure #%d)", pole_id, pole.failure_count)

        return pole

    @staticmethod
    async def mark_repaired(
        db: AsyncSession,
        pole_id: str,
        repair_notes: str | None = None,
        cost: float | None = None,
    ) -> StreetlightPole | None:
        """Mark a pole as repaired and operational."""
        stmt = select(StreetlightPole).where(StreetlightPole.pole_id == pole_id)
        result = await db.execute(stmt)
        pole = result.scalar_one_or_none()

        if pole:
            pole.is_operational = True
            pole.last_maintenance = datetime.now(UTC)
            # Schedule next maintenance 6 months out
            pole.next_maintenance_due = datetime.now(UTC) + timedelta(days=180)

            history = pole.maintenance_history or []
            entry: dict[str, Any] = {
                'date': datetime.now(UTC).isoformat(),
                'type': 'repair',
                'notes': repair_notes or 'Repair completed',
            }
            if cost:
                entry['cost'] = cost
            history.append(entry)
            pole.maintenance_history = history

            await db.commit()
            await db.refresh(pole)

        return pole

    @staticmethod
    async def predict_maintenance(
        db: AsyncSession,
        *,
        city: str | None = None,
        top_n: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Simple predictive maintenance scoring.

        Score based on:
        - Failure frequency (failure_count)
        - Time since last maintenance
        - Overdue maintenance flag
        - Pole age

        Returns top_n poles most likely to need maintenance.
        """
        stmt = select(StreetlightPole).where(StreetlightPole.is_operational)
        if city:
            stmt = stmt.where(StreetlightPole.city == city)

        result = await db.execute(stmt)
        poles = result.scalars().all()

        scored: list[dict[str, Any]] = []
        now = datetime.now(UTC)

        for pole in poles:
            risk = 0.0

            # Failure frequency
            if pole.failure_count >= 5:
                risk += 0.35
            elif pole.failure_count >= 3:
                risk += 0.20
            elif pole.failure_count >= 1:
                risk += 0.10

            # Maintenance overdue
            if pole.next_maintenance_due:
                due = pole.next_maintenance_due
                if due.tzinfo is None:
                    due = due.replace(tzinfo=UTC)
                if now > due:
                    overdue_days = (now - due).days
                    risk += min(0.30, overdue_days * 0.01)

            # Time since last maintenance
            if pole.last_maintenance:
                lm = pole.last_maintenance
                if lm.tzinfo is None:
                    lm = lm.replace(tzinfo=UTC)
                days_since = (now - lm).days
                if days_since > 365:
                    risk += 0.20
                elif days_since > 180:
                    risk += 0.10

            # Pole age
            if pole.installation_date:
                inst = pole.installation_date
                if inst.tzinfo is None:
                    inst = inst.replace(tzinfo=UTC)
                age_years = (now - inst).days / 365
                if age_years > 10:
                    risk += 0.15
                elif age_years > 5:
                    risk += 0.05

            risk = min(risk, 1.0)

            if risk > 0.1:
                scored.append({
                    'pole_id': pole.pole_id,
                    'qr_code': pole.qr_code,
                    'city': pole.city,
                    'ward_id': pole.ward_id,
                    'risk_score': round(risk, 3),
                    'failure_count': pole.failure_count,
                    'is_operational': pole.is_operational,
                    'last_maintenance': pole.last_maintenance.isoformat() if pole.last_maintenance else None,
                })

        scored.sort(key=lambda x: x['risk_score'], reverse=True)
        return scored[:top_n]

    @staticmethod
    async def get_city_stats(db: AsyncSession, city: str) -> dict[str, Any]:
        """Get aggregate streetlight statistics for a city."""
        base = select(func.count(StreetlightPole.id)).where(StreetlightPole.city == city)

        total = (await db.execute(base)).scalar() or 0
        operational = (await db.execute(
            base.where(StreetlightPole.is_operational)
        )).scalar() or 0
        non_operational = total - operational

        return {
            'city': city,
            'total_poles': total,
            'operational': operational,
            'non_operational': non_operational,
            'operational_rate': round(operational / max(total, 1) * 100, 1),
        }
