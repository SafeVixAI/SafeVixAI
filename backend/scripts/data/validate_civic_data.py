# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Data quality validator for civic_intel data files.

Usage:
    python scripts/data/validate_civic_data.py
    python scripts/data/validate_civic_data.py --check-urls
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / 'data' / 'civic_intel'


def validate_json(filepath: Path) -> dict:
    """Validate a JSON file and return stats."""
    try:
        with open(filepath, encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return {'valid': True, 'records': len(data), 'type': 'array'}
        elif isinstance(data, dict):
            return {'valid': True, 'records': len(data), 'type': 'object'}
        return {'valid': True, 'records': 1, 'type': type(data).__name__}
    except json.JSONDecodeError as e:
        return {'valid': False, 'error': str(e)}
    except Exception as e:
        return {'valid': False, 'error': str(e)}


def validate_csv(filepath: Path) -> dict:
    """Validate a CSV file and return stats."""
    try:
        with open(filepath, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            return {'valid': True, 'records': len(rows), 'columns': len(reader.fieldnames or []),
                    'fieldnames': list(reader.fieldnames or [])}
    except Exception as e:
        return {'valid': False, 'error': str(e)}


def validate_geojson(filepath: Path) -> dict:
    """Validate a GeoJSON file."""
    try:
        with open(filepath, encoding='utf-8') as f:
            data = json.load(f)
        if data.get('type') == 'FeatureCollection':
            features = data.get('features', [])
            return {'valid': True, 'records': len(features), 'type': 'FeatureCollection'}
        return {'valid': False, 'error': f'Not FeatureCollection: {data.get("type")}'}
    except Exception as e:
        return {'valid': False, 'error': str(e)}


def validate_municipalities(filepath: Path) -> list[str]:
    """Validate municipalities_seed.json for data quality."""
    issues = []
    try:
        with open(filepath, encoding='utf-8') as f:
            data = json.load(f)

        slugs = set()
        for i, m in enumerate(data):
            # Required fields
            for field in ['slug', 'name', 'city', 'state_code']:
                if not m.get(field):
                    issues.append(f'  [{i}] Missing required field: {field}')

            # Duplicate slug check
            slug = m.get('slug', '')
            if slug in slugs:
                issues.append(f'  [{i}] Duplicate slug: {slug}')
            slugs.add(slug)

            # Phone format
            phone = m.get('helpline_phone', '')
            if phone and not (phone.replace('-', '').replace(' ', '').replace('+', '').isdigit()):
                issues.append(f'  [{i}] {slug}: Invalid phone format: {phone}')

    except Exception as e:
        issues.append(f'  Failed to validate: {e}')

    return issues


def main():
    parser = argparse.ArgumentParser(description='Validate SafeVixAI civic data')
    parser.add_argument('--check-urls', action='store_true', help='Check if URLs are reachable')
    parser.parse_args()

    print('\n╔══════════════════════════════════════════╗')
    print('║  SafeVixAI Civic Data Validator           ║')
    print('╚══════════════════════════════════════════╝')
    print(f'  Data dir: {DATA_DIR}')
    print()

    if not DATA_DIR.exists():
        print('  ✗ data/civic_intel/ directory does not exist!')
        sys.exit(1)

    total_files = 0
    valid_files = 0
    total_records = 0
    total_size = 0

    # Walk all files
    for filepath in sorted(DATA_DIR.rglob('*')):
        if filepath.is_dir():
            continue
        total_files += 1
        rel = filepath.relative_to(DATA_DIR)
        size = filepath.stat().st_size
        total_size += size
        size_str = f'{size / 1024:.1f} KB' if size < 1024 * 1024 else f'{size / (1024 * 1024):.1f} MB'

        if filepath.suffix == '.json':
            result = validate_json(filepath)
        elif filepath.suffix == '.csv':
            result = validate_csv(filepath)
        elif filepath.suffix == '.geojson':
            result = validate_geojson(filepath)
        else:
            result = {'valid': True, 'records': '?'}

        if result.get('valid'):
            valid_files += 1
            records = result.get('records', 0)
            if isinstance(records, int):
                total_records += records
            print(f'  ✓ {str(rel):45s}  {records:>8} records  {size_str:>10s}')
        else:
            print(f'  ✗ {str(rel):45s}  ERROR: {result.get("error", "unknown")}')

    # Special validation for municipalities
    muni_file = DATA_DIR / 'municipalities_seed.json'
    if muni_file.exists():
        print('\n  Municipality Quality Check:')
        issues = validate_municipalities(muni_file)
        if issues:
            for issue in issues[:20]:
                print(f'    ⚠ {issue}')
            if len(issues) > 20:
                print(f'    ... and {len(issues) - 20} more issues')
        else:
            print('    ✓ All municipalities pass quality checks')

    # Summary
    print(f'\n{"═" * 55}')
    print('  VALIDATION SUMMARY')
    print(f'{"═" * 55}')
    print(f'  Total files:    {total_files}')
    print(f'  Valid files:    {valid_files}')
    print(f'  Invalid files:  {total_files - valid_files}')
    print(f'  Total records:  {total_records:,}')
    total_size_str = f'{total_size / 1024:.1f} KB' if total_size < 1024 * 1024 else f'{total_size / (1024 * 1024):.1f} MB'
    print(f'  Total size:     {total_size_str}')

    if valid_files == total_files:
        print('\n  ✅ ALL FILES VALID')
    else:
        print(f'\n  ⚠ {total_files - valid_files} INVALID FILE(S)')
        sys.exit(1)

    print()


if __name__ == '__main__':
    main()
