# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import argparse
import csv
import json
import urllib.parse
import urllib.request
from collections.abc import Iterable
from pathlib import Path

DEFAULT_ENDPOINTS = (
    'https://overpass-api.de/api/interpreter',
    'https://overpass.kumi.systems/api/interpreter',
    'https://lz4.overpass-api.de/api/interpreter',
)
DEFAULT_HEADERS = {
    'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
    'User-Agent': 'SafeVixAI bootstrap scripts/1.0',
}
CSV_COLUMNS = [
    'osm_id',
    'osm_type',
    'name',
    'lat',
    'lon',
    'phone',
    'type',
    'city',
    'state',
    'address',
    'opening_hours',
    'website',
    'source',
]


def build_arg_parser(description: str, default_output: Path) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '--output',
        type=Path,
        default=default_output,
        help=f'CSV path to write. Defaults to {default_output}',
    )
    parser.add_argument(
        '--endpoint',
        help='Optional Overpass endpoint override. Defaults to a built-in fallback list.',
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='HTTP timeout in seconds. Defaults to 300.',
    )
    return parser


def build_india_query(selectors: Iterable[str], *, timeout: int) -> str:
    joined_selectors = '\n  '.join(selector.strip() for selector in selectors if selector.strip())
    return (
        f'[out:json][timeout:{timeout}];\n'
        'area["ISO3166-1"="IN"][admin_level=2]->.searchArea;\n'
        '(\n'
        f'  {joined_selectors}\n'
        ');\n'
        'out center tags;'
    )


def fetch_elements(query: str, *, endpoint: str | None, timeout: int, **kwargs) -> list[dict]:
    payload = urllib.parse.urlencode({'data': query}).encode('utf-8')
    endpoints = [endpoint] if endpoint else list(DEFAULT_ENDPOINTS)
    last_error: Exception | None = None

    for url in endpoints:
        request = urllib.request.Request(url, data=payload, headers=DEFAULT_HEADERS, method='POST')
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                decoded = response.read().decode('utf-8')
            data = json.loads(decoded)
            return list(data.get('elements', []))
        except Exception as exc:  # pragma: no cover - network failure path
            last_error = exc

    raise SystemExit(f'Unable to fetch data from Overpass. Last error: {last_error}')


def extract_point(element: dict) -> tuple[float | None, float | None]:
    if 'lat' in element and 'lon' in element:
        return float(element['lat']), float(element['lon'])

    center = element.get('center') or {}
    if 'lat' in center and 'lon' in center:
        return float(center['lat']), float(center['lon'])

    return None, None


def compose_address(tags: dict[str, str]) -> str:
    parts = [
        tags.get('addr:housenumber'),
        tags.get('addr:street'),
        tags.get('addr:suburb'),
        tags.get('addr:city') or tags.get('addr:town') or tags.get('addr:village'),
        tags.get('addr:state'),
    ]
    return ', '.join(part for part in parts if part)


def normalize_row(element: dict, *, default_type: str, fallback_name: str, **kwargs) -> dict | None:
    lat, lon = extract_point(element)
    if lat is None or lon is None:
        return None

    tags = element.get('tags', {})
    amenity_type = tags.get('amenity') or tags.get('healthcare') or tags.get('emergency') or default_type
    return {
        'osm_id': str(element.get('id', '')),
        'osm_type': str(element.get('type', '')),
        'name': tags.get('name') or fallback_name,
        'lat': f'{lat:.6f}',
        'lon': f'{lon:.6f}',
        'phone': tags.get('phone') or tags.get('contact:phone') or tags.get('emergency:phone') or '',
        'type': amenity_type,
        'city': tags.get('addr:city') or tags.get('addr:town') or tags.get('addr:village') or '',
        'state': tags.get('addr:state') or '',
        'address': compose_address(tags),
        'opening_hours': tags.get('opening_hours') or '',
        'website': tags.get('website') or tags.get('contact:website') or '',
        'source': 'overpass',
    }


def dedupe_rows(rows: Iterable[dict]) -> list[dict]:
    seen: set[tuple[str, str, str, str]] = set()
    deduped: list[dict] = []
    for row in rows:
        key = (
            row.get('name', '').strip().lower(),
            row.get('type', '').strip().lower(),
            row.get('lat', ''),
            row.get('lon', ''),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    deduped.sort(key=lambda item: (item['state'], item['city'], item['name']))
    return deduped


def write_rows(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    materialized = dedupe_rows(rows)
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(materialized)
    return len(materialized)
