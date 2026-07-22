# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.admin_boundary import AdminBoundary
from models.grievance import Grievance
from models.lgd_entity import LGDEntity
from models.municipality import Municipality
from models.osm_civic_feature import OSMCivicFeature

logger = logging.getLogger(__name__)


class CivicAnalyticsService:
    """Enterprise domain service encapsulating civic intelligence analytics and statistics."""

    @staticmethod
    async def get_civic_stats(db: AsyncSession, state_code: str | None) -> dict[str, Any]:
        """Get aggregated civic intelligence statistics."""
        if state_code:
            sc = state_code.upper()

        # Count LGD entities
        lgd_stmt = select(func.count(LGDEntity.id))
        if state_code:
            lgd_stmt = lgd_stmt.where(LGDEntity.state_code == sc)
        lgd_count = (await db.execute(lgd_stmt)).scalar() or 0

        # Count boundaries
        boundary_stmt = select(func.count(AdminBoundary.id))
        if state_code:
            boundary_stmt = boundary_stmt.where(AdminBoundary.state_code == sc)
        boundary_count = (await db.execute(boundary_stmt)).scalar() or 0

        # Count OSM features by type
        osm_stmt = select(
            OSMCivicFeature.feature_type,
            func.count(OSMCivicFeature.id),
        ).group_by(OSMCivicFeature.feature_type)
        osm_result = await db.execute(osm_stmt)
        osm_counts = {r[0]: r[1] for r in osm_result.all()}

        # Count grievances by category
        grv_stmt = select(
            Grievance.category,
            func.count(Grievance.id),
        )
        if state_code:
            grv_stmt = grv_stmt.where(Grievance.state_code == sc)
        grv_stmt = grv_stmt.group_by(Grievance.category)
        grv_result = await db.execute(grv_stmt)
        grv_counts = {r[0]: r[1] for r in grv_result.all()}

        # Count municipalities
        muni_stmt = select(func.count(Municipality.id))
        if state_code:
            muni_stmt = muni_stmt.where(Municipality.state_code == sc)
        muni_count = (await db.execute(muni_stmt)).scalar() or 0

        return {
            'state_code': state_code,
            'lgd_entities': lgd_count,
            'admin_boundaries': boundary_count,
            'osm_features': osm_counts,
            'grievances': grv_counts,
            'municipalities': muni_count,
        }

    @staticmethod
    async def get_municipality_stats(db: AsyncSession, slug: str) -> dict[str, Any]:
        """Get local complaint/grievance stats for a municipality."""
        result = await db.execute(
            select(Municipality).where(Municipality.slug == slug)
        )
        m = result.scalar_one_or_none()
        if not m:
            raise HTTPException(status_code=404, detail='Municipality not found')

        # Count grievances for this state
        grv_stmt = select(
            Grievance.category,
            Grievance.status,
            func.count(Grievance.id),
        ).where(
            Grievance.state_code == m.state_code
        ).group_by(Grievance.category, Grievance.status)

        grv_result = await db.execute(grv_stmt)
        grv_data = [
            {'category': r[0], 'status': r[1], 'count': r[2]}
            for r in grv_result.all()
        ]

        # Count OSM features in city
        osm_stmt = select(
            OSMCivicFeature.feature_type,
            func.count(OSMCivicFeature.id),
        ).where(
            OSMCivicFeature.city == m.city
        ).group_by(OSMCivicFeature.feature_type)

        osm_result = await db.execute(osm_stmt)
        osm_data = {r[0]: r[1] for r in osm_result.all()}

        return {
            'slug': slug,
            'city': m.city,
            'grievances': grv_data,
            'infrastructure': osm_data,
        }
