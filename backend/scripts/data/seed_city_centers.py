# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Seed the city_centers table from the hardcoded default list.

Usage:
    python -m scripts.data.seed_city_centers   # (requires async DB session)
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from core.database import AsyncSessionLocal
from models.city_center import CityCenter
from services.city_center_repo import _HARDCODED_CENTERS, _OFFLINE_CENTERS

logger = logging.getLogger(__name__)

_DISPLAY_NAMES: dict[str, str] = {
    'agartala': 'Agartala',
    'agra': 'Agra',
    'ahmedabad': 'Ahmedabad',
    'aizawl': 'Aizawl',
    'amritsar': 'Amritsar',
    'bengaluru': 'Bengaluru',
    'bhopal': 'Bhopal',
    'bhubaneswar': 'Bhubaneswar',
    'chandigarh': 'Chandigarh',
    'chennai': 'Chennai',
    'coimbatore': 'Coimbatore',
    'dehradun': 'Dehradun',
    'delhi': 'Delhi',
    'gangtok': 'Gangtok',
    'gurugram': 'Gurugram',
    'guwahati': 'Guwahati',
    'hyderabad': 'Hyderabad',
    'imphal': 'Imphal',
    'indore': 'Indore',
    'itanagar': 'Itanagar',
    'jaipur': 'Jaipur',
    'jammu': 'Jammu',
    'kochi': 'Kochi',
    'kohima': 'Kohima',
    'kolkata': 'Kolkata',
    'lucknow': 'Lucknow',
    'madurai': 'Madurai',
    'mangaluru': 'Mangaluru',
    'mumbai': 'Mumbai',
    'mysuru': 'Mysuru',
    'nagpur': 'Nagpur',
    'noida': 'Noida',
    'panaji': 'Panaji',
    'patna': 'Patna',
    'pune': 'Pune',
    'raipur': 'Raipur',
    'ranchi': 'Ranchi',
    'shillong': 'Shillong',
    'siliguri': 'Siliguri',
    'srinagar': 'Srinagar',
    'surat': 'Surat',
    'thiruvananthapuram': 'Thiruvananthapuram',
    'tiruchirappalli': 'Tiruchirappalli',
    'vadodara': 'Vadodara',
    'varanasi': 'Varanasi',
    'vijayawada': 'Vijayawada',
    'visakhapatnam': 'Visakhapatnam',
}


async def seed() -> int:
    """Insert all city_centers rows. Returns count of new records."""
    async with AsyncSessionLocal() as db:
        existing = (await db.execute(select(CityCenter.city_slug))).scalars().all()
        existing_set = set(existing)

        count = 0
        for slug, (lat, lon) in _HARDCODED_CENTERS.items():
            if slug in existing_set:
                continue
            record = CityCenter(
                city_slug=slug,
                display_name=_DISPLAY_NAMES.get(slug, slug.title()),
                lat=lat,
                lon=lon,
                is_offline_bundle=slug in _OFFLINE_CENTERS,
                state=None,
            )
            db.add(record)
            count += 1

        if count:
            await db.commit()
            logger.info("Seeded %d city_centers (skipped %d existing)", count, len(existing))
        else:
            logger.info("All %d city_centers already exist — nothing to seed", len(existing))

        return count


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed())
