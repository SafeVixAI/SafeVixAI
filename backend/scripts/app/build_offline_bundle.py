# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import argparse
import asyncio

from core.config import get_settings
from core.database import AsyncSessionLocal
from core.redis_client import create_cache
from scripts.app.seed_emergency import CITY_GROUPS
from services.emergency_locator import CITY_CENTERS, EmergencyLocatorService
from services.overpass_service import OverpassService


async def build_bundle(city: str) -> tuple[str, int]:
    settings = get_settings()
    cache = create_cache(settings.redis_url)
    overpass_service = OverpassService(settings)
    emergency_service = EmergencyLocatorService(
        settings=settings,
        cache=cache,
        overpass_service=overpass_service,
    )

    try:
        async with AsyncSessionLocal() as session:
            bundle = await emergency_service.build_city_bundle(db=session, city=city)
        bundle_path = settings.offline_bundle_dir / f'{city.strip().lower()}.json'
        return str(bundle_path), len(bundle['services'])
    finally:
        await overpass_service.aclose()
        await cache.close()


async def main() -> None:
    parser = argparse.ArgumentParser(description='Build offline emergency bundles from the current database state.')
    parser.add_argument('cities', nargs='*', help='City names to build. Defaults to all supported city centers.')
    parser.add_argument('--group', action='append', choices=sorted(CITY_GROUPS.keys()), help='Build bundles for one or more predefined city groups.')
    args = parser.parse_args()

    requested_cities = {city.strip().lower() for city in args.cities}
    for group in args.group or []:
        requested_cities.update(CITY_GROUPS[group])
    cities = sorted(requested_cities) if requested_cities else sorted(CITY_CENTERS.keys())
    for city in cities:
        output_path, count = await build_bundle(city)
        print(f'Built offline bundle for {city}: {count} services -> {output_path}')


if __name__ == '__main__':
    asyncio.run(main())
