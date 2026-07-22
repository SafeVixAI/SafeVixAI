# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Generate frontend civic_features_summary.json from downloaded OSM data.

Reads all CSVs from data/civic_intel/osm_features/ and creates a lightweight
summary for the frontend /civic-intel dashboard when backend is offline.

Usage:
    python scripts/data/generate_frontend_civic_summary.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OSM_DIR = PROJECT_ROOT / 'data' / 'civic_intel' / 'osm_features'
FRONTEND_OUT = PROJECT_ROOT.parent / 'frontend' / 'public' / 'offline-data'


def main():
    FRONTEND_OUT.mkdir(parents=True, exist_ok=True)

    if not OSM_DIR.exists():
        print('No OSM features directory found')
        return

    # Parse all CSV files: {city}_{feature_type}.csv
    summary = {}
    total_features = 0

    for csv_file in sorted(OSM_DIR.glob('*.csv')):
        parts = csv_file.stem.rsplit('_', 1)
        if len(parts) != 2:
            continue
        city, feature_type = parts

        try:
            with open(csv_file, encoding='utf-8') as f:
                count = sum(1 for _ in csv.reader(f)) - 1  # minus header
        except Exception:
            count = 0

        if count > 0:
            summary.setdefault(city, {})
            summary[city][feature_type] = count
            total_features += count

    # Add total per city
    for city in summary:
        summary[city]['_total'] = sum(v for k, v in summary[city].items() if k != '_total')

    # Write output
    out_file = FRONTEND_OUT / 'civic_features_summary.json'
    out_file.write_text(json.dumps(summary, indent=2), encoding='utf-8')

    print(f'Cities: {len(summary)}')
    print(f'Total features: {total_features:,}')
    print(f'Output: {out_file}')

    for city, counts in sorted(summary.items(), key=lambda x: x[1].get('_total', 0), reverse=True):
        total = counts.get('_total', 0)
        top = sorted([(k, v) for k, v in counts.items() if k != '_total'], key=lambda x: x[1], reverse=True)[:3]
        top_str = ', '.join(f'{k}={v}' for k, v in top)
        print(f'  {city:20s} {total:>6,}  [{top_str}]')


if __name__ == '__main__':
    main()
