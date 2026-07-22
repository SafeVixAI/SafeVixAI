# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import logging

from geoalchemy2 import WKTElement
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.road_issue import RoadIssue
from models.ward import Ward

logger = logging.getLogger(__name__)

# Predefined GCC Wards / Zones for Chennai seeding
GCC_DEMO_WARDS = [
    {
        "ward_id": "ward_05_royapuram",
        "ward_name": "Royapuram Ward 50",
        "zone_name": "Zone 5 (Royapuram)",
        "city": "Chennai",
        "state_code": "TN",
        "boundary_wkt": "POLYGON((80.26 13.07, 80.30 13.07, 80.30 13.11, 80.26 13.11, 80.26 13.07))",
        "population": 45000,
        "area_sqkm": 4.5
    },
    {
        "ward_id": "ward_08_anna_nagar",
        "ward_name": "Anna Nagar Ward 104",
        "zone_name": "Zone 8 (Anna Nagar)",
        "city": "Chennai",
        "state_code": "TN",
        "boundary_wkt": "POLYGON((80.20 13.06, 80.26 13.06, 80.26 13.10, 80.20 13.10, 80.20 13.06))",
        "population": 60000,
        "area_sqkm": 5.2
    },
    {
        "ward_id": "ward_09_teynampet",
        "ward_name": "Teynampet Ward 118",
        "zone_name": "Zone 9 (Teynampet)",
        "city": "Chennai",
        "state_code": "TN",
        "boundary_wkt": "POLYGON((80.23 13.02, 80.28 13.02, 80.28 13.07, 80.23 13.07, 80.23 13.02))",
        "population": 55000,
        "area_sqkm": 4.8
    },
    {
        "ward_id": "ward_10_kodambakkam",
        "ward_name": "Kodambakkam Ward 130",
        "zone_name": "Zone 10 (Kodambakkam)",
        "city": "Chennai",
        "state_code": "TN",
        "boundary_wkt": "POLYGON((80.19 13.01, 80.23 13.01, 80.23 13.06, 80.19 13.06, 80.19 13.01))",
        "population": 58000,
        "area_sqkm": 5.0
    },
    {
        "ward_id": "ward_13_adyar",
        "ward_name": "Adyar Ward 172",
        "zone_name": "Zone 13 (Adyar)",
        "city": "Chennai",
        "state_code": "TN",
        "boundary_wkt": "POLYGON((80.22 12.96, 80.27 12.96, 80.27 13.02, 80.22 13.02, 80.22 12.96))",
        "population": 52000,
        "area_sqkm": 6.1
    }
]


class WardService:
    @staticmethod
    async def ensure_seeded(db: AsyncSession) -> None:
        """Seed demo wards if the wards table is empty."""
        stmt = select(func.count(Ward.id))
        count = (await db.execute(stmt)).scalar() or 0
        if count == 0:
            logger.info("Seeding demo Chennai wards in WardService...")
            for w in GCC_DEMO_WARDS:
                ward = Ward(
                    ward_id=w["ward_id"],
                    ward_name=w["ward_name"],
                    zone_name=w["zone_name"],
                    city=w["city"],
                    state_code=w["state_code"],
                    boundary=WKTElement(w["boundary_wkt"], srid=4326),
                    population=w["population"],
                    area_sqkm=w["area_sqkm"]
                )
                db.add(ward)
            await db.commit()
            logger.info("Demo Chennai wards successfully seeded.")

    @classmethod
    async def find_ward_by_coordinates(cls, db: AsyncSession, lat: float, lon: float) -> Ward | None:
        """Find the ward containing the given lat/lon coordinates."""
        await cls.ensure_seeded(db)

        # Point is lon, lat in PostGIS
        point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        stmt = select(Ward).where(func.ST_Contains(Ward.boundary, point)).limit(1)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_ward_stats(db: AsyncSession, ward_id: str) -> dict:
        """Get complaint statistics for a specific ward."""
        # Open issues count
        open_stmt = select(func.count(RoadIssue.id)).where(
            RoadIssue.ward_id == ward_id,
            RoadIssue.status.in_(["open", "acknowledged", "in_progress"])
        )
        open_count = (await db.execute(open_stmt)).scalar() or 0

        # Resolved issues count
        resolved_stmt = select(func.count(RoadIssue.id)).where(
            RoadIssue.ward_id == ward_id,
            RoadIssue.status == "resolved"
        )
        resolved_count = (await db.execute(resolved_stmt)).scalar() or 0

        # Rejected issues count
        rejected_stmt = select(func.count(RoadIssue.id)).where(
            RoadIssue.ward_id == ward_id,
            RoadIssue.status == "rejected"
        )
        rejected_count = (await db.execute(rejected_stmt)).scalar() or 0

        total = open_count + resolved_count + rejected_count
        resolution_rate = (resolved_count / total * 100.0) if total > 0 else 0.0

        return {
            "ward_id": ward_id,
            "open_issues": open_count,
            "resolved_issues": resolved_count,
            "rejected_issues": rejected_count,
            "total_issues": total,
            "resolution_rate": round(resolution_rate, 2)
        }

    @staticmethod
    async def list_all_wards(db: AsyncSession) -> list[Ward]:
        """List all wards registered in the system."""
        await WardService.ensure_seeded(db)
        stmt = select(Ward).order_by(Ward.ward_name.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())
