# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Repository for CityCenter records — DB-backed with hardcoded fallback."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import select

from models.city_center import CityCenter

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ── Hardcoded fallback (used when DB is unavailable) ──────────────────────
_HARDCODED_CENTERS: dict[str, tuple[float, float]] = {
    'agartala': (23.8315, 91.2868),
    'agra': (27.1767, 78.0081),
    'ahmedabad': (23.0225, 72.5714),
    'aizawl': (23.7271, 92.7176),
    'amritsar': (31.6340, 74.8723),
    'bengaluru': (12.9716, 77.5946),
    'bhopal': (23.2599, 77.4126),
    'bhubaneswar': (20.2961, 85.8245),
    'chandigarh': (30.7333, 76.7794),
    'chennai': (13.0827, 80.2707),
    'coimbatore': (11.0168, 76.9558),
    'dehradun': (30.3165, 78.0322),
    'delhi': (28.6139, 77.2090),
    'gangtok': (27.3389, 88.6065),
    'gurugram': (28.4595, 77.0266),
    'guwahati': (26.1445, 91.7362),
    'hyderabad': (17.3850, 78.4867),
    'imphal': (24.8170, 93.9368),
    'indore': (22.7196, 75.8577),
    'itanagar': (27.0844, 93.6053),
    'jaipur': (26.9124, 75.7873),
    'jammu': (32.7266, 74.8570),
    'kochi': (9.9312, 76.2673),
    'kohima': (25.6751, 94.1086),
    'kolkata': (22.5726, 88.3639),
    'lucknow': (26.8467, 80.9462),
    'madurai': (9.9252, 78.1198),
    'mangaluru': (12.9141, 74.8560),
    'mumbai': (19.0760, 72.8777),
    'mysuru': (12.2958, 76.6394),
    'nagpur': (21.1458, 79.0882),
    'noida': (28.5355, 77.3910),
    'panaji': (15.4909, 73.8278),
    'patna': (25.5941, 85.1376),
    'pune': (18.5204, 73.8567),
    'raipur': (21.2514, 81.6296),
    'ranchi': (23.3441, 85.3096),
    'shillong': (25.5788, 91.8933),
    'siliguri': (26.7271, 88.3953),
    'srinagar': (34.0837, 74.7973),
    'surat': (21.1702, 72.8311),
    'thiruvananthapuram': (8.5241, 76.9366),
    'tiruchirappalli': (10.7905, 78.7047),
    'vadodara': (22.3072, 73.1812),
    'varanasi': (25.3176, 82.9739),
    'vijayawada': (16.5062, 80.6480),
    'visakhapatnam': (17.6868, 83.2185),
}

# Subset included in PWA offline emergency bundles
_OFFLINE_CENTERS: dict[str, tuple[float, float]] = {
    slug: _HARDCODED_CENTERS[slug]
    for slug in [
        'chennai', 'coimbatore', 'madurai', 'thiruvananthapuram', 'kochi',
        'bengaluru', 'mumbai', 'pune', 'nagpur', 'hyderabad', 'delhi',
        'jaipur', 'ahmedabad', 'surat', 'vadodara', 'kolkata', 'patna',
        'bhopal', 'indore', 'lucknow', 'agra', 'varanasi', 'chandigarh',
        'visakhapatnam', 'bhubaneswar',
    ]
}


async def get_all_city_centers(
    db: AsyncSession | None = None,
) -> dict[str, tuple[float, float]]:
    """Return all city centers — DB-backed if available, hardcoded fallback.

    Result is slug -> (lat, lon).
    """
    if db is None:
        return dict(_HARDCODED_CENTERS)

    try:
        rows = (await db.execute(select(CityCenter))).scalars().all()
        if rows:
            return {row.city_slug: (row.lat, row.lon) for row in rows}
    except Exception:
        logger.warning("CityCenter DB query failed; using hardcoded fallback", exc_info=True)

    return dict(_HARDCODED_CENTERS)


async def get_offline_centers(
    db: AsyncSession | None = None,
) -> dict[str, tuple[float, float]]:
    """Return city centers included in offline bundles.

    DB-backed if available, hardcoded fallback otherwise.
    """
    if db is None:
        return dict(_OFFLINE_CENTERS)

    try:
        rows = (
            (await db.execute(
                select(CityCenter).where(CityCenter.is_offline_bundle == True)  # noqa: E712
            ))
            .scalars()
            .all()
        )
        if rows:
            return {row.city_slug: (row.lat, row.lon) for row in rows}
    except Exception:
        logger.warning("CityCenter offline query failed; using hardcoded fallback", exc_info=True)

    return dict(_OFFLINE_CENTERS)


async def get_city_center(
    slug: str,
    db: AsyncSession | None = None,
) -> tuple[float, float] | None:
    """Return (lat, lon) for a single city slug, or None if not found."""
    if db is not None:
        try:
            row = (
                await db.execute(
                    select(CityCenter).where(CityCenter.city_slug == slug)
                )
            ).scalar_one_or_none()
            if row:
                return (row.lat, row.lon)
        except Exception:
            logger.warning("CityCenter lookup failed for %s; using hardcoded fallback", slug)

    return _HARDCODED_CENTERS.get(slug)
