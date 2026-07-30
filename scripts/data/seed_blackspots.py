# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT_DIR / 'chatbot_service' / 'data' / 'accidents' / 'morth_2022'
DEFAULT_OUTPUT_CSV = ROOT_DIR / 'chatbot_service' / 'data' / 'accidents' / 'accident_blackspots_preview.csv'
DEFAULT_OUTPUT_GEOJSON = ROOT_DIR / 'frontend' / 'public' / 'offline-data' / 'accident-blackspots.geojson'
STATE_CENTROIDS = {
    'andhra pradesh': (15.9129, 79.74),
    'arunachal pradesh': (28.2180, 94.7278),
    'assam': (26.2006, 92.9376),
    'bihar': (25.0961, 85.3131),
    'chhattisgarh': (21.2787, 81.8661),
    'delhi': (28.7041, 77.1025),
    'goa': (15.2993, 74.1240),
    'gujarat': (22.2587, 71.1924),
    'haryana': (29.0588, 76.0856),
    'himachal pradesh': (31.1048, 77.1734),
    'jharkhand': (23.6102, 85.2799),
    'karnataka': (15.3173, 75.7139),
    'kerala': (10.8505, 76.2711),
    'madhya pradesh': (22.9734, 78.6569),
    'maharashtra': (19.7515, 75.7139),
    'manipur': (24.6637, 93.9063),
    'meghalaya': (25.4670, 91.3662),
    'mizoram': (23.1645, 92.9376),
    'nagaland': (26.1584, 94.5624),
    'odisha': (20.9517, 85.0985),
    'punjab': (31.1471, 75.3412),
    'rajasthan': (27.0238, 74.2179),
    'sikkim': (27.5330, 88.5122),
    'tamil nadu': (11.1271, 78.6569),
    'telangana': (18.1124, 79.0193),
    'tripura': (23.9408, 91.9882),
    'uttar pradesh': (26.8467, 80.9462),
    'uttarakhand': (30.0668, 79.0193),
    'west bengal': (22.9868, 87.8550),
}
STATE_FIELDS = ('state', 'state_name', 'state_ut', 'state/ut', 'state_ut_name')
CITY_FIELDS = ('city', 'city_name', 'district', 'district_name', 'location')
LAT_FIELDS = ('lat', 'latitude')
LON_FIELDS = ('lon', 'lng', 'longitude')
ACCIDENT_FIELDS = ('total_accidents', 'accidents', 'road_accidents', 'fatal_accidents')
DEATH_FIELDS = ('persons_killed', 'killed', 'deaths')
INJURY_FIELDS = ('persons_injured', 'injured')


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


def _parse_int(value: str) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _discover_csvs(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(candidate for candidate in path.rglob('*.csv') if candidate.is_file())


def _normalize_row(row: dict[str, str], *, source_file: str, index: int) -> dict | None:
    state = _first_value(row, STATE_FIELDS)
    city = _first_value(row, CITY_FIELDS)
    lat = _parse_float(_first_value(row, LAT_FIELDS))
    lon = _parse_float(_first_value(row, LON_FIELDS))

    if (lat is None or lon is None) and state.lower() in STATE_CENTROIDS:
        lat, lon = STATE_CENTROIDS[state.lower()]

    if lat is None or lon is None:
        return None

    accidents = _parse_int(_first_value(row, ACCIDENT_FIELDS))
    killed = _parse_int(_first_value(row, DEATH_FIELDS))
    injured = _parse_int(_first_value(row, INJURY_FIELDS))
    severity_score = accidents + (2 * killed) + injured

    return {
        'blackspot_id': f'{source_file}:{index}',
        'state': state,
        'city': city,
        'lat': f'{lat:.6f}',
        'lon': f'{lon:.6f}',
        'accidents': accidents,
        'killed': killed,
        'injured': injured,
        'severity_score': severity_score,
        'source_file': source_file,
    }


def _load_records(input_path: Path) -> list[dict]:
    records: list[dict] = []
    for csv_path in _discover_csvs(input_path):
        with csv_path.open('r', encoding='utf-8', newline='') as handle:
            reader = csv.DictReader(handle)
            for index, row in enumerate(reader, start=1):
                normalized = _normalize_row(row, source_file=csv_path.name, index=index)
                if normalized is not None:
                    records.append(normalized)
    return records


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=['blackspot_id', 'state', 'city', 'lat', 'lon', 'accidents', 'killed', 'injured', 'severity_score', 'source_file'],
        )
        writer.writeheader()
        writer.writerows(rows)


def _write_geojson(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    geojson = {
        'type': 'FeatureCollection',
        'features': [
            {
                'type': 'Feature',
                'geometry': {'type': 'Point', 'coordinates': [float(row['lon']), float(row['lat'])]},
                'properties': {
                    'blackspot_id': row['blackspot_id'],
                    'state': row['state'],
                    'city': row['city'],
                    'accidents': row['accidents'],
                    'killed': row['killed'],
                    'injured': row['injured'],
                    'severity_score': row['severity_score'],
                    'source_file': row['source_file'],
                },
            }
            for row in rows
        ],
    }
    path.write_text(json.dumps(geojson, indent=2), encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Normalize accident CSVs into a blackspot preview CSV and GeoJSON bundle.',
    )
    parser.add_argument('--input', type=Path, default=DEFAULT_INPUT, help=f'CSV file or directory. Defaults to {DEFAULT_INPUT}')
    parser.add_argument('--output-csv', type=Path, default=DEFAULT_OUTPUT_CSV, help=f'Normalized CSV output. Defaults to {DEFAULT_OUTPUT_CSV}')
    parser.add_argument(
        '--output-geojson',
        type=Path,
        default=DEFAULT_OUTPUT_GEOJSON,
        help=f'GeoJSON output for offline mapping. Defaults to {DEFAULT_OUTPUT_GEOJSON}',
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f'Input path not found: {args.input}')

    rows = _load_records(args.input)
    if not rows:
        raise SystemExit('No accident CSV rows could be normalized from the provided input.')

    rows.sort(key=lambda item: item['severity_score'], reverse=True)
    _write_csv(args.output_csv, rows)
    _write_geojson(args.output_geojson, rows)
    print(f'Wrote {len(rows)} normalized blackspot rows to {args.output_csv}')
    print(f'Wrote GeoJSON preview to {args.output_geojson}')


if __name__ == '__main__':
    main()
