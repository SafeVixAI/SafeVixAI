# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

from geoalchemy2.elements import WKTElement
from sqlalchemy.dialects.postgresql import insert

from core.config import get_settings
from core.database import AsyncSessionLocal
from models.emergency import EmergencyService
from services.emergency_locator import CITY_CENTERS, OFFLINE_CITY_CENTERS
from services.overpass_service import OverpassService

OFFLINE_DIR = Path(__file__).resolve().parent / 'offline'
FRONTEND_GEOJSON_PATH = Path(__file__).resolve().parents[2] / 'frontend' / 'public' / 'offline-data' / 'india-emergency.geojson'
CITY_GROUPS: dict[str, list[str]] = {
    'metros': ['bengaluru', 'chennai', 'delhi', 'hyderabad', 'kolkata', 'mumbai', 'pune'],
    'south': ['bengaluru', 'chennai', 'coimbatore', 'hyderabad', 'kochi', 'madurai', 'mysuru', 'thiruvananthapuram', 'tiruchirappalli', 'vijayawada', 'visakhapatnam'],
    'north': ['chandigarh', 'dehradun', 'delhi', 'gurugram', 'jaipur', 'jammu', 'lucknow', 'noida', 'srinagar'],
    'east': ['agartala', 'bhubaneswar', 'gangtok', 'guwahati', 'imphal', 'itanagar', 'kolkata', 'patna', 'ranchi', 'shillong', 'siliguri'],
    'west': ['ahmedabad', 'amritsar', 'bhopal', 'indore', 'mumbai', 'nagpur', 'panaji', 'pune', 'raipur', 'surat'],
    'pan_india': sorted(OFFLINE_CITY_CENTERS.keys()),
}


def _service_to_feature(city: str, service) -> dict:
    return {
        'type': 'Feature',
        'id': f'{city}:{service.id}',
        'geometry': {
            'type': 'Point',
            'coordinates': [service.lon, service.lat],
        },
        'properties': {
            'city': city.title(),
            'name': service.name,
            'category': service.category,
            'sub_category': service.sub_category,
            'phone': service.phone,
            'phone_emergency': service.phone_emergency,
            'address': service.address,
            'has_trauma': service.has_trauma,
            'has_icu': service.has_icu,
            'is_24hr': service.is_24hr,
            'source': service.source,
        },
    }


def _write_geojson(path: Path, *, cities: list[str], features: list[dict]) -> None:
    payload = {
        'type': 'FeatureCollection',
        'properties': {
            'generated_at': datetime.now(UTC).replace(tzinfo=None).isoformat(timespec='seconds') + 'Z',
            'cities': [city.title() for city in cities],
            'source': 'overpass',
            'feature_count': len(features),
        },
        'features': features,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding='utf-8')


async def seed_city(city: str, lat: float, lon: float, *, export_offline: bool, limit: int) -> tuple[int, list[dict]]:
    settings = get_settings()
    overpass_service = OverpassService(settings)
    try:
        services = await overpass_service.search_services(
            lat=lat,
            lon=lon,
            radius=settings.max_radius,
            categories=['hospital', 'police', 'ambulance', 'fire', 'towing', 'pharmacy'],
            limit=limit,
        )
    finally:
        await overpass_service.aclose()

    rows: list[dict] = []
    seen_osm_ids: set[int] = set()
    for service in services:
        osm_id = int(service.id) if str(service.id).isdigit() else None
        if osm_id is not None and osm_id in seen_osm_ids:
            continue
        if osm_id is not None:
            seen_osm_ids.add(osm_id)

        rows.append(
            {
                'osm_id': osm_id,
                'osm_type': 'node_or_way',
                'name': service.name,
                'category': service.category,
                'sub_category': service.sub_category,
                'address': service.address,
                'phone': service.phone,
                'phone_emergency': service.phone_emergency,
                'location': WKTElement(f'POINT({service.lon} {service.lat})', srid=4326),
                'city': city.title(),
                'district': city.title(),
                'country_code': 'IN',
                'is_24hr': service.is_24hr,
                'has_trauma': service.has_trauma,
                'has_icu': service.has_icu,
                'source': 'overpass',
                'raw_tags': None,
                'verified': False,
            }
        )

    async with AsyncSessionLocal() as session:
        if rows:
            stmt = insert(EmergencyService).values(rows)
            upsert = stmt.on_conflict_do_update(
                index_elements=['osm_id'],
                set_={
                    'name': stmt.excluded.name,
                    'category': stmt.excluded.category,
                    'sub_category': stmt.excluded.sub_category,
                    'address': stmt.excluded.address,
                    'phone': stmt.excluded.phone,
                    'phone_emergency': stmt.excluded.phone_emergency,
                    'location': stmt.excluded.location,
                    'city': stmt.excluded.city,
                    'district': stmt.excluded.district,
                    'is_24hr': stmt.excluded.is_24hr,
                    'has_trauma': stmt.excluded.has_trauma,
                    'has_icu': stmt.excluded.has_icu,
                    'source': stmt.excluded.source,
                },
            )
            await session.execute(upsert)
            await session.commit()

    if export_offline:
        OFFLINE_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            'city': city.title(),
            'center': {'lat': lat, 'lon': lon},
            'services': [service.model_dump(mode='json') for service in services],
        }
        (OFFLINE_DIR / f'{city.lower()}.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')

    return len(rows), [_service_to_feature(city, service) for service in services]


async def main() -> None:
    parser = argparse.ArgumentParser(description='Seed emergency services from Overpass for major Indian cities.')
    parser.add_argument('--city', action='append', help='One or more city keys to seed. Defaults to the 25-city offline set.')
    parser.add_argument('--group', action='append', choices=sorted(CITY_GROUPS.keys()), help='Seed one or more predefined city groups.')
    parser.add_argument('--export-offline', action='store_true', help='Export per-city JSON bundles for offline use.')
    parser.add_argument(
        '--geojson-output',
        type=Path,
        default=FRONTEND_GEOJSON_PATH,
        help=f'Combined GeoJSON bundle output path. Defaults to {FRONTEND_GEOJSON_PATH}',
    )
    parser.add_argument('--skip-geojson', action='store_true', help='Skip writing the combined frontend GeoJSON bundle.')
    parser.add_argument('--limit', type=int, default=300, help='Maximum emergency records to ingest per city (default: 300).')
    args = parser.parse_args()

    requested_cities = {city.strip().lower() for city in (args.city or [])}
    for group in args.group or []:
        requested_cities.update(CITY_GROUPS[group])

    if not requested_cities:
        requested_cities = set(OFFLINE_CITY_CENTERS.keys())

    requested = sorted(requested_cities)
    missing = [city for city in requested if city not in CITY_CENTERS]
    if missing:
        raise SystemExit(f'Unknown cities: {", ".join(missing)}')

    total = 0
    geojson_features: list[dict] = []
    for city in requested:
        lat, lon = CITY_CENTERS[city]
        seeded, features = await seed_city(city, lat, lon, export_offline=args.export_offline, limit=max(50, args.limit))
        total += seeded
        geojson_features.extend(features)
        print(f'Seeded {seeded:3d} emergency services for {city.title()}')

    if not args.skip_geojson:
        _write_geojson(args.geojson_output, cities=requested, features=geojson_features)
        print(f'Wrote {len(geojson_features)} GeoJSON features to {args.geojson_output}')

    print(f'Total inserted or refreshed rows: {total}')


if __name__ == '__main__':
    asyncio.run(main())
