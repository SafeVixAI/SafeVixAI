# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import argparse
import asyncio
import logging

from core.config import get_settings
from core.database import AsyncSessionLocal
from core.redis_client import create_cache
from services.emergency_locator import OFFLINE_CITY_CENTERS, EmergencyLocatorService
from services.overpass_service import OverpassService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

async def generate_bundles(cities_filter: list[str] | None = None) -> None:
    settings = get_settings()

    # Ensure nested output directories exist
    settings.offline_bundle_dir.mkdir(parents=True, exist_ok=True)

    cache = create_cache(settings.redis_url)
    overpass = OverpassService(settings)
    locator = EmergencyLocatorService(
        settings=settings,
        cache=cache,
        overpass_service=overpass,
    )

    cities_to_process = list(OFFLINE_CITY_CENTERS.keys())
    if cities_filter:
        cities_to_process = [c for c in cities_to_process if c in cities_filter]

    if not cities_to_process:
        logger.warning("No cities matched your filter. Check spelling.")
        return

    logger.info(f"Generating offline bundles for {len(cities_to_process)} cities...")

    success_count = 0
    for idx, city in enumerate(cities_to_process, 1):
        try:
            logger.info(f"[{idx}/{len(cities_to_process)}] Processing {city}...")
            async with AsyncSessionLocal() as db:
                bundle = await locator.build_city_bundle(db=db, city=city)

            service_count = len(bundle.get("services", []))
            source = bundle.get("source", "unknown")
            output_file = settings.offline_bundle_dir / f"{city.lower()}.json"

            logger.info(
                f"  -> SUCCESS ({city}): Fetched {service_count} services "
                f"from '{source}'. Saved to {output_file.name}"
            )
            success_count += 1

            # Be gentle with Overpass rate limits if processing many cities
            if idx < len(cities_to_process):
                await asyncio.sleep(2.0)

        except Exception as e:
            logger.exception("  -> ERROR (%s): %s", city, str(e))

    await cache.close()
    if hasattr(overpass, 'close'):
        await overpass.close()

    logger.info(f"Build complete. Successfully processed {success_count}/{len(cities_to_process)} cities.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate offline PWA city JSON bundles")
    parser.add_argument(
        "--cities",
        type=str,
        help="Comma-separated list of cities to generate (e.g., chennai,delhi,mumbai)"
    )
    args = parser.parse_args()

    filter_list = None
    if args.cities:
        filter_list = [c.strip().lower() for c in args.cities.split(",") if c.strip()]

    asyncio.run(generate_bundles(cities_filter=filter_list))
