# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / 'backend'

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from core.database import AsyncSessionLocal
from geoalchemy2.elements import WKTElement
from models.emergency import EmergencyService
from sqlalchemy.dialects.postgresql import insert

DEFAULT_CSV = ROOT_DIR / 'chatbot_service' / 'data' / 'hospitals' / 'hospital_directory.csv'
STATE_CODES = {
    'andaman and nicobar islands': 'AN',
    'andhra pradesh': 'AP',
    'arunachal pradesh': 'AR',
    'assam': 'AS',
    'bihar': 'BR',
    'chandigarh': 'CH',
    'chhattisgarh': 'CG',
    'dadra and nagar haveli and daman and diu': 'DN',
    'delhi': 'DL',
    'goa': 'GA',
    'gujarat': 'GJ',
    'haryana': 'HR',
    'himachal pradesh': 'HP',
    'jammu and kashmir': 'JK',
    'jharkhand': 'JH',
    'karnataka': 'KA',
    'kerala': 'KL',
    'ladakh': 'LA',
    'lakshadweep': 'LD',
    'madhya pradesh': 'MP',
    'maharashtra': 'MH',
    'manipur': 'MN',
    'meghalaya': 'ML',
    'mizoram': 'MZ',
    'nagaland': 'NL',
    'odisha': 'OD',
    'puducherry': 'PY',
    'punjab': 'PB',
    'rajasthan': 'RJ',
    'sikkim': 'SK',
    'tamil nadu': 'TN',
    'telangana': 'TS',
    'tripura': 'TR',
    'uttar pradesh': 'UP',
    'uttarakhand': 'UK',
    'west bengal': 'WB',
}


def _first_value(row: dict[str, str], names: tuple[str, ...]) -> str:
    for name in names:
        value = (row.get(name) or '').strip()
        if value:
            return value
    return ''


def _parse_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _stable_osm_id(name: str, lat: float, lon: float, city: str, state: str) -> int:
    key = f'{name}|{lat:.6f}|{lon:.6f}|{city}|{state}'
    digest = hashlib.blake2b(key.encode('utf-8'), digest_size=8).hexdigest()
    return int(digest, 16) % 9_000_000_000_000_000_000


def _load_rows(csv_path: Path, *, category: str, source: str) -> list[dict]:
    rows: list[dict] = []
    with csv_path.open('r', encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            name = _first_value(raw, ('name', 'hospital_name'))
            lat = _parse_float(_first_value(raw, ('lat', 'latitude')))
            lon = _parse_float(_first_value(raw, ('lon', 'longitude', 'lng')))
            if not name or lat is None or lon is None:
                continue

            city = _first_value(raw, ('city', 'district'))
            state = _first_value(raw, ('state', 'province'))
            sub_category = _first_value(raw, ('type', 'category', 'sub_category'))
            address = _first_value(raw, ('address',))
            state_code = STATE_CODES.get(state.lower())
            osm_id_raw = _first_value(raw, ('osm_id', 'id'))
            osm_id = int(osm_id_raw) if osm_id_raw.isdigit() else _stable_osm_id(name, lat, lon, city, state)

            tag_blob = ' '.join(part for part in [name, sub_category, address] if part).lower()
            rows.append(
                {
                    'osm_id': osm_id,
                    'osm_type': _first_value(raw, ('osm_type',)) or 'csv_import',
                    'name': name,
                    'category': category,
                    'sub_category': sub_category or None,
                    'address': address or None,
                    'phone': _first_value(raw, ('phone', 'contact_phone')) or None,
                    'phone_emergency': _first_value(raw, ('phone_emergency', 'emergency_phone')) or None,
                    'location': WKTElement(f'POINT({lon} {lat})', srid=4326),
                    'city': city or None,
                    'district': _first_value(raw, ('district',)) or city or None,
                    'state': state or None,
                    'state_code': state_code,
                    'country_code': 'IN',
                    'is_24hr': '24' in _first_value(raw, ('opening_hours', 'hours')),
                    'has_trauma': 'trauma' in tag_blob,
                    'has_icu': 'icu' in tag_blob or 'intensive care' in tag_blob,
                    'source': source,
                    'raw_tags': {key: value for key, value in raw.items() if value},
                    'verified': True,
                }
            )
    return rows


async def _seed_rows(rows: list[dict]) -> int:
    if not rows:
        return 0

    async with AsyncSessionLocal() as session:
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
                'state': stmt.excluded.state,
                'state_code': stmt.excluded.state_code,
                'is_24hr': stmt.excluded.is_24hr,
                'has_trauma': stmt.excluded.has_trauma,
                'has_icu': stmt.excluded.has_icu,
                'source': stmt.excluded.source,
                'raw_tags': stmt.excluded.raw_tags,
                'verified': stmt.excluded.verified,
            },
        )
        await session.execute(upsert)
        await session.commit()
    return len(rows)


async def _async_main(args: argparse.Namespace) -> None:
    csv_path = args.csv.resolve()
    if not csv_path.exists():
        raise SystemExit(f'CSV not found: {csv_path}')

    rows = _load_rows(csv_path, category=args.category, source=args.source)
    seeded = await _seed_rows(rows)
    print(f'Seeded {seeded} emergency service rows from {csv_path}')


def main() -> None:
    parser = argparse.ArgumentParser(description='Seed hospital CSV data into emergency_services.')
    parser.add_argument('--csv', type=Path, default=DEFAULT_CSV, help=f'CSV input path. Defaults to {DEFAULT_CSV}')
    parser.add_argument('--category', default='hospital', help='Category to use for inserted rows. Defaults to hospital.')
    parser.add_argument('--source', default='nhp_osm', help='Source label to store in PostgreSQL. Defaults to nhp_osm.')
    args = parser.parse_args()
    asyncio.run(_async_main(args))


if __name__ == '__main__':
    main()
