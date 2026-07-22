# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Fetch ward boundary polygons for major cities from OpenStreetMap.

Usage:
    python scripts/data/fetch_ward_boundaries.py [--city chennai]

Fetches admin boundary polygons at admin_level=10 (wards) from Overpass.
"""

from __future__ import annotations

import argparse
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
OUTPUT_DIR = PROJECT_ROOT / 'data' / 'civic_intel' / 'ward_boundaries'
BBOXES_FILE = PROJECT_ROOT / 'data' / 'civic_intel' / 'city_bboxes.json'

OVERPASS_URL = 'https://overpass-api.de/api/interpreter'

# City-specific admin_level for ward boundaries
# India: admin_level 10 = ward, 8 = municipal corporation, 9 = zone
CITY_ADMIN_LEVELS = {
    'chennai': 10,
    'mumbai': 10,
    'delhi': 10,
    'bengaluru': 10,
    'hyderabad': 10,
    'kolkata': 10,
    'pune': 10,
    'ahmedabad': 10,
}


def build_ward_query(bbox: list[float], admin_level: int = 10) -> str:
    """Build Overpass query for ward boundaries."""
    s, w, n, e = bbox
    return f"""[out:json][timeout:180];
(
  relation["boundary"="administrative"]["admin_level"="{admin_level}"]({s},{w},{n},{e});
);
out body;
>;
out skel qt;"""


def elements_to_geojson(elements: list[dict]) -> dict:
    """Convert Overpass elements to GeoJSON FeatureCollection.
    
    This handles the raw node/way/relation format from Overpass.
    """
    # Index nodes by id
    nodes = {}
    ways_map = {}
    relations = []

    for el in elements:
        if el['type'] == 'node':
            nodes[el['id']] = [el['lon'], el['lat']]
        elif el['type'] == 'way':
            ways_map[el['id']] = el.get('nodes', [])
        elif el['type'] == 'relation':
            relations.append(el)

    features = []
    for rel in relations:
        tags = rel.get('tags', {})
        name = tags.get('name', tags.get('name:en', f'Ward {rel["id"]}'))

        # Build polygon from relation members
        outer_coords = []
        for member in rel.get('members', []):
            if member.get('role') == 'outer' and member.get('type') == 'way':
                way_id = member['ref']
                if way_id in ways_map:
                    way_nodes = ways_map[way_id]
                    coords = [nodes[nid] for nid in way_nodes if nid in nodes]
                    if coords:
                        outer_coords.extend(coords)

        if len(outer_coords) >= 3:
            # Close the polygon if needed
            if outer_coords[0] != outer_coords[-1]:
                outer_coords.append(outer_coords[0])

            feature = {
                'type': 'Feature',
                'properties': {
                    'ward_name': name,
                    'ward_number': tags.get('ref', tags.get('admin_ref', '')),
                    'admin_level': tags.get('admin_level', ''),
                    'osm_relation_id': rel['id'],
                    'name_local': tags.get('name:ta', tags.get('name:hi', tags.get('name:te', ''))),
                    'population': tags.get('population', ''),
                },
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [outer_coords],
                }
            }
            features.append(feature)

    return {
        'type': 'FeatureCollection',
        'features': features,
    }


def main():
    parser = argparse.ArgumentParser(description='Fetch ward boundary polygons')
    parser.add_argument('--city', default='chennai', help='City name (default: chennai)')
    parser.add_argument('--all', action='store_true', help='Fetch all configured cities')
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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

    if args.all:
        cities = [c for c in CITY_ADMIN_LEVELS if c in all_bboxes]
    else:
        cities = [args.city]

    print()
    print('=' * 56)
    print('  SafeVixAI Ward Boundary Fetcher')
    print('=' * 56)

    for city in cities:
        if city not in all_bboxes:
            print(f"  SKIP {city}: no bbox data")
            continue

        admin_level = CITY_ADMIN_LEVELS.get(city, 10)
        print(f"\n  Fetching {city} (admin_level={admin_level})...")

        bbox = all_bboxes[city]
        query = build_ward_query(bbox, admin_level)

        try:
            with httpx.Client(follow_redirects=True) as c:
                r = c.get(
                    OVERPASS_URL,
                    params={'data': query},
                    headers={'User-Agent': 'SafeVixAI-CivicIntel/1.0'},
                    timeout=180,
                )
                r.raise_for_status()
                data = r.json()
                elements = data.get('elements', [])

                if elements:
                    geojson = elements_to_geojson(elements)
                    outfile = OUTPUT_DIR / f'{city}.geojson'
                    outfile.write_text(json.dumps(geojson), encoding='utf-8')
                    kb = outfile.stat().st_size / 1024
                    print(f"  OK  {city}: {len(geojson['features'])} wards, {kb:.1f} KB")
                else:
                    print(f"  EMPTY {city}: no ward boundaries found at admin_level={admin_level}")

        except Exception as e:
            print(f"  ERR  {city}: {e}")

        time.sleep(3)  # Overpass courtesy

    print()


if __name__ == '__main__':
    main()
