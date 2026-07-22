# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Fetch road network classification data from OpenStreetMap Overpass API.

Usage:
    python scripts/data/fetch_road_network.py [--cities mumbai,chennai] [--all]

Fetches road classification data (motorway/trunk/primary/secondary/tertiary/residential)
and maps each to Indian road authority ownership.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

try:
    import httpx
except ImportError:
    print("ERROR: httpx required. Run: pip install httpx")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / 'data' / 'civic_intel' / 'road_network'
BBOXES_FILE = PROJECT_ROOT / 'data' / 'civic_intel' / 'city_bboxes.json'

OVERPASS_URL = 'https://overpass-api.de/api/interpreter'

# Indian road authority mapping
AUTHORITY_MAP = {
    'motorway': {'authority': 'NHAI', 'category': 'Expressway', 'maintenance': 'Central'},
    'motorway_link': {'authority': 'NHAI', 'category': 'Expressway Ramp', 'maintenance': 'Central'},
    'trunk': {'authority': 'NHAI', 'category': 'National Highway', 'maintenance': 'Central'},
    'trunk_link': {'authority': 'NHAI', 'category': 'NH Ramp', 'maintenance': 'Central'},
    'primary': {'authority': 'State PWD', 'category': 'State Highway', 'maintenance': 'State'},
    'primary_link': {'authority': 'State PWD', 'category': 'SH Ramp', 'maintenance': 'State'},
    'secondary': {'authority': 'State PWD', 'category': 'Major District Road', 'maintenance': 'State'},
    'secondary_link': {'authority': 'State PWD', 'category': 'MDR Link', 'maintenance': 'State'},
    'tertiary': {'authority': 'Municipal Corporation', 'category': 'Other District Road', 'maintenance': 'Municipal'},
    'tertiary_link': {'authority': 'Municipal Corporation', 'category': 'ODR Link', 'maintenance': 'Municipal'},
    'residential': {'authority': 'Municipal Corporation', 'category': 'Residential Street', 'maintenance': 'Municipal'},
    'unclassified': {'authority': 'Municipal/Panchayat', 'category': 'Village Road', 'maintenance': 'Local'},
    'living_street': {'authority': 'Municipal Corporation', 'category': 'Residential', 'maintenance': 'Municipal'},
    'service': {'authority': 'Private/Municipal', 'category': 'Service Road', 'maintenance': 'Private'},
}

ROAD_TYPES = ['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'residential']


def build_road_query(bbox: list[float]) -> str:
    """Build Overpass query for road network."""
    s, w, n, e = bbox
    type_filter = '|'.join(ROAD_TYPES)
    return f"""[out:json][timeout:120];
(
  way["highway"~"^({type_filter})(_link)?$"]({s},{w},{n},{e});
);
out tags center;"""


def fetch_roads(city: str, bbox: list[float]) -> list[dict]:
    """Fetch road data for a city."""
    query = build_road_query(bbox)
    try:
        with httpx.Client(follow_redirects=True) as c:
            r = c.get(
                OVERPASS_URL,
                params={'data': query},
                headers={'User-Agent': 'SafeVixAI-CivicIntel/1.0'},
                timeout=120,
            )
            r.raise_for_status()
            data = r.json()
            elements = data.get('elements', [])

            roads = []
            for el in elements:
                tags = el.get('tags', {})
                highway = tags.get('highway', '')
                center = el.get('center', {})

                auth_info = AUTHORITY_MAP.get(highway, {
                    'authority': 'Unknown',
                    'category': highway,
                    'maintenance': 'Unknown',
                })

                roads.append({
                    'osm_id': el.get('id', 0),
                    'name': tags.get('name', tags.get('ref', '')),
                    'name_local': tags.get('name:hi', tags.get('name:ta', tags.get('name:te', ''))),
                    'highway_type': highway,
                    'road_category': auth_info['category'],
                    'authority': auth_info['authority'],
                    'maintenance_level': auth_info['maintenance'],
                    'ref': tags.get('ref', ''),
                    'lanes': tags.get('lanes', ''),
                    'surface': tags.get('surface', ''),
                    'maxspeed': tags.get('maxspeed', ''),
                    'oneway': tags.get('oneway', ''),
                    'lit': tags.get('lit', ''),
                    'center_lat': center.get('lat', ''),
                    'center_lon': center.get('lon', ''),
                    'city': city,
                })
            return roads
    except Exception as e:
        print(f"  ERR {city}: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description='Fetch road network classification')
    parser.add_argument('--cities', help='Comma-separated city names')
    parser.add_argument('--all', action='store_true', help='Process all cities')
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load bboxes
    if not BBOXES_FILE.exists():
        print(f"ERROR: {BBOXES_FILE} not found")
        sys.exit(1)

    with open(BBOXES_FILE, encoding='utf-8') as f:
        raw_bboxes = json.load(f)

    metro_data = raw_bboxes.get('metros', raw_bboxes)
    all_bboxes = {}
    for city_name, city_info in metro_data.items():
        if isinstance(city_info, dict) and 'bbox' in city_info:
            all_bboxes[city_name] = city_info['bbox']
        elif isinstance(city_info, list):
            all_bboxes[city_name] = city_info

    if args.cities:
        cities = [c.strip() for c in args.cities.split(',')]
    elif args.all:
        cities = sorted(all_bboxes.keys())
    else:
        cities = sorted(all_bboxes.keys())[:5]  # Default: top 5

    print()
    print('=' * 56)
    print('  SafeVixAI Road Network Classifier')
    print('=' * 56)
    print(f'  Cities: {len(cities)}')
    print(f'  Output: {OUTPUT_DIR}')
    print()

    summary = {}
    csv_fields = [
        'osm_id', 'name', 'name_local', 'highway_type', 'road_category',
        'authority', 'maintenance_level', 'ref', 'lanes', 'surface',
        'maxspeed', 'oneway', 'lit', 'center_lat', 'center_lon', 'city'
    ]

    for i, city in enumerate(cities):
        if city not in all_bboxes:
            print(f"  SKIP {city}: no bbox")
            continue

        print(f"[{i+1}/{len(cities)}] Fetching {city}...")
        roads = fetch_roads(city, all_bboxes[city])

        if roads:
            outfile = OUTPUT_DIR / f'{city}_roads.csv'
            with open(outfile, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=csv_fields)
                writer.writeheader()
                writer.writerows(roads)

            # Count by type
            by_type = {}
            for r in roads:
                t = r['highway_type']
                by_type[t] = by_type.get(t, 0) + 1
            summary[city] = {
                'total': len(roads),
                'by_type': by_type,
            }
            top_types = sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:3]
            top_str = ', '.join(f'{t}={c}' for t, c in top_types)
            print(f"  OK  {city}: {len(roads):,} roads [{top_str}]")
        else:
            print(f"  EMPTY {city}")

        time.sleep(2)  # Be respectful to Overpass

    # Save summary
    summary_file = OUTPUT_DIR / 'road_network_summary.json'
    summary_file.write_text(json.dumps(summary, indent=2), encoding='utf-8')

    total = sum(v['total'] for v in summary.values())
    print()
    print(f'  Total: {len(summary)} cities, {total:,} road segments')
    print(f'  Output: {OUTPUT_DIR}')
    print()


if __name__ == '__main__':
    main()
