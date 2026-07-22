# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Standalone OSM civic feature fetcher — dumps to data/civic_intel/osm_features/.

No database needed. Reads city_bboxes.json and queries Overpass API for civic
infrastructure: streetlights, traffic signals, bus stops, speed bumps, CCTV,
zebra crossings, toll booths.

Usage:
    python scripts/data/fetch_osm_civic_features.py
    python scripts/data/fetch_osm_civic_features.py --cities mumbai,chennai,delhi
    python scripts/data/fetch_osm_civic_features.py --all
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

try:
    import httpx
except ImportError:
    print('[ERROR] httpx is required. Run: pip install httpx')
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / 'data' / 'civic_intel'
BBOXES_FILE = DATA_DIR / 'city_bboxes.json'
OUTPUT_DIR = DATA_DIR / 'osm_features'

OVERPASS_URL = os.getenv('OVERPASS_URL', 'https://overpass-api.de/api/interpreter')

# OSM feature queries — maps feature_type to Overpass tag filters
FEATURE_QUERIES = {
    'streetlight': 'node["highway"="street_lamp"]',
    'traffic_signal': 'node["highway"="traffic_signals"]',
    'bus_stop': 'node["highway"="bus_stop"]',
    'speed_bump': 'node["traffic_calming"="bump"]',
    'cctv': 'node["man_made"="surveillance"]["surveillance:type"="camera"]',
    'zebra_crossing': 'node["highway"="crossing"]["crossing"="zebra"]',
    'toll_booth': 'node["barrier"="toll_booth"]',
    'police_station': 'node["amenity"="police"]',
    'fire_station': 'node["amenity"="fire_station"]',
    'hospital': 'node["amenity"="hospital"]',
    'fuel_station': 'node["amenity"="fuel"]',
    'parking': 'node["amenity"="parking"]',
}


def build_overpass_query(bbox: list[float], feature_filter: str) -> str:
    """Build Overpass QL query for a bounding box."""
    s, w, n, e = bbox
    return f'[out:json][timeout:60];({feature_filter}({s},{w},{n},{e}););out center;'


def fetch_features_for_city(
    client: httpx.Client,
    city: str,
    bbox: list[float],
    feature_types: list[str] | None = None,
) -> dict[str, list[dict]]:
    """Fetch all feature types for a city."""
    results: dict[str, list[dict]] = {}
    types_to_fetch = feature_types or list(FEATURE_QUERIES.keys())

    for ftype in types_to_fetch:
        if ftype not in FEATURE_QUERIES:
            print(f'  ⚠ Unknown feature type: {ftype}')
            continue

        query = build_overpass_query(bbox, FEATURE_QUERIES[ftype])
        try:
            resp = client.get(
                OVERPASS_URL,
                params={'data': query},
                headers={'User-Agent': 'SafeVixAI-CivicIntel/1.0'},
                timeout=90,
            )
            resp.raise_for_status()
            data = resp.json()
            elements = data.get('elements', [])

            features = []
            for el in elements:
                lat = el.get('lat') or el.get('center', {}).get('lat')
                lon = el.get('lon') or el.get('center', {}).get('lon')
                if lat and lon:
                    features.append({
                        'osm_id': el.get('id'),
                        'lat': round(lat, 6),
                        'lon': round(lon, 6),
                        'feature_type': ftype,
                        'city': city,
                        'tags': json.dumps(el.get('tags', {})),
                    })

            results[ftype] = features
            print(f'  ✓ {city}/{ftype}: {len(features)} features')

            # Rate limit: 1 request per second (Overpass courtesy)
            time.sleep(1.2)

        except httpx.TimeoutException:
            print(f'  ✗ {city}/{ftype}: TIMEOUT (bbox may be too large)')
            results[ftype] = []
        except Exception as exc:
            print(f'  ✗ {city}/{ftype}: {exc}')
            results[ftype] = []

    return results


def save_features(city: str, features: dict[str, list[dict]]) -> dict[str, int]:
    """Save features to CSV files, one per feature type."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    counts = {}

    for ftype, items in features.items():
        counts[ftype] = len(items)
        if not items:
            continue

        outfile = OUTPUT_DIR / f'{city}_{ftype}.csv'
        fieldnames = ['osm_id', 'lat', 'lon', 'feature_type', 'city', 'tags']
        with open(outfile, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(items)

    return counts


def main():
    parser = argparse.ArgumentParser(description='Fetch OSM civic features for Indian cities')
    parser.add_argument('--cities', type=str, help='Comma-separated city names (e.g., mumbai,chennai)')
    parser.add_argument('--all', action='store_true', help='Fetch for all cities in city_bboxes.json')
    parser.add_argument('--features', type=str, help='Comma-separated feature types to fetch')
    args = parser.parse_args()

    # Load city bounding boxes
    if not BBOXES_FILE.exists():
        print(f'[ERROR] City bboxes file not found: {BBOXES_FILE}')
        sys.exit(1)

    with open(BBOXES_FILE, encoding='utf-8') as f:
        raw_bboxes = json.load(f)

    # city_bboxes.json has nested structure: {"metros": {"mumbai": {"bbox": [...], ...}}}
    metro_data = raw_bboxes.get('metros', raw_bboxes)
    all_bboxes = {}
    for city_name, city_info in metro_data.items():
        if isinstance(city_info, dict) and 'bbox' in city_info:
            all_bboxes[city_name] = city_info['bbox']
        elif isinstance(city_info, list):
            all_bboxes[city_name] = city_info

    # Determine which cities to process
    if args.cities:
        city_names = [c.strip().lower() for c in args.cities.split(',')]
    elif args.all:
        city_names = list(all_bboxes.keys())
    else:
        # Default: top 10 metro cities
        top_metros = ['mumbai', 'delhi', 'chennai', 'kolkata', 'bengaluru',
                      'hyderabad', 'ahmedabad', 'pune', 'jaipur', 'lucknow']
        city_names = [c for c in top_metros if c in all_bboxes]

    feature_types = [f.strip() for f in args.features.split(',')] if args.features else None

    print('\n╔══════════════════════════════════════════╗')
    print('║  SafeVixAI OSM Civic Feature Fetcher     ║')
    print('╚══════════════════════════════════════════╝')
    print(f'  Cities: {len(city_names)}')
    print(f'  Features: {", ".join(feature_types) if feature_types else "all"}')
    print(f'  Output: {OUTPUT_DIR}')
    print(f'  Overpass: {OVERPASS_URL}')
    print()

    summary: dict[str, dict[str, int]] = {}

    with httpx.Client() as client:
        for i, city in enumerate(city_names, 1):
            if city not in all_bboxes:
                print(f'[{i}/{len(city_names)}] ⚠ {city}: not in city_bboxes.json — skipping')
                continue

            bbox = all_bboxes[city]
            print(f'[{i}/{len(city_names)}] Fetching {city}...')
            features = fetch_features_for_city(client, city, bbox, feature_types)
            counts = save_features(city, features)
            summary[city] = counts

            # Extra pause between cities
            if i < len(city_names):
                time.sleep(2)

    # Save summary
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_file = OUTPUT_DIR / 'features_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    # Print summary
    print(f'\n{"═" * 55}')
    print('  SUMMARY')
    print(f'{"═" * 55}')
    total_all = 0
    for city, counts in summary.items():
        total_city = sum(counts.values())
        total_all += total_city
        top_features = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:3]
        top_str = ', '.join(f'{k}={v}' for k, v in top_features if v > 0)
        print(f'  {city:20s}  {total_city:>6,} features  [{top_str}]')

    print(f'{"─" * 55}')
    print(f'  {"TOTAL":20s}  {total_all:>6,} features')
    print(f'  Output: {OUTPUT_DIR}')
    print()


if __name__ == '__main__':
    main()
