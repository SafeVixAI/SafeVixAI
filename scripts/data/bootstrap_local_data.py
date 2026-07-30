# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import struct
import sys
import zipfile
from io import BytesIO
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / 'backend'

import importlib.util as _ilu


def _load_backend_module(rel_path: str, module_name: str):
    """Load a module from backend/ by explicit file path and register it in
    sys.modules under *module_name*.  This makes the import fully transparent
    to Pylance/Pyright (no opaque sys.path mutation) while still satisfying
    Python internals that need __module__ to be resolvable (e.g. dataclasses
    with slots=True).
    """
    abs_path = BACKEND_ROOT / rel_path
    spec = _ilu.spec_from_file_location(module_name, abs_path)
    mod = _ilu.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules[module_name] = mod  # register BEFORE exec so __module__ resolves
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


_seed_viol = _load_backend_module("scripts/data/seed_violations.py", "scripts.seed_violations")
DEFAULT_RULES = _seed_viol.DEFAULT_RULES
OVERRIDE_COLUMNS = _seed_viol.OVERRIDE_COLUMNS
RULE_COLUMNS = _seed_viol.RULE_COLUMNS
_load_override_rows = _seed_viol._load_override_rows
_load_rule_rows = _seed_viol._load_rule_rows
_rule_to_row = _seed_viol._rule_to_row
_write_csv = _seed_viol._write_csv

_emerg_catalog = _load_backend_module("services/local_emergency_catalog.py", "services.local_emergency_catalog")
load_local_emergency_catalog = _emerg_catalog.load_local_emergency_catalog



CHATBOT_DATA_DIR = PROJECT_ROOT / 'chatbot_service' / 'data'
FRONTEND_OFFLINE_DIR = PROJECT_ROOT / 'frontend' / 'public' / 'offline-data'
BACKEND_CHALLAN_DIR = PROJECT_ROOT / 'backend' / 'datasets' / 'challan'
ROADS_DIR = CHATBOT_DATA_DIR / 'roads'
PMGSY_MAX_POINTS_PER_SEGMENT = 24

OFFLINE_CITY_CENTERS: dict[str, tuple[float, float]] = {
    'chennai': (13.0827, 80.2707),
    'coimbatore': (11.0168, 76.9558),
    'madurai': (9.9252, 78.1198),
    'thiruvananthapuram': (8.5241, 76.9366),
    'kochi': (9.9312, 76.2673),
    'bengaluru': (12.9716, 77.5946),
    'mumbai': (19.0760, 72.8777),
    'pune': (18.5204, 73.8567),
    'nagpur': (21.1458, 79.0882),
    'hyderabad': (17.3850, 78.4867),
    'delhi': (28.6139, 77.2090),
    'jaipur': (26.9124, 75.7873),
    'ahmedabad': (23.0225, 72.5714),
    'surat': (21.1702, 72.8311),
    'vadodara': (22.3072, 73.1812),
    'kolkata': (22.5726, 88.3639),
    'patna': (25.5941, 85.1376),
    'bhopal': (23.2599, 77.4126),
    'indore': (22.7196, 75.8577),
    'lucknow': (26.8467, 80.9462),
    'agra': (27.1767, 78.0081),
    'varanasi': (25.3176, 82.9739),
    'chandigarh': (30.7333, 76.7794),
    'visakhapatnam': (17.6868, 83.2185),
    'bhubaneswar': (20.2961, 85.8245),
}
CITY_RADIUS_METERS = 80_000


def sync_challan_assets() -> None:
    rules_source = CHATBOT_DATA_DIR / 'violations_seed.csv'
    overrides_source = CHATBOT_DATA_DIR / 'state_overrides.csv'
    rule_map = {rule.violation_code: _rule_to_row(rule) for rule in DEFAULT_RULES}
    if rules_source.exists():
        for row in _load_rule_rows(rules_source):
            existing = rule_map.get(row['violation_code'])
            rule_map[row['violation_code']] = _seed_viol._merge_rule_rows(existing, row) if existing else row
    override_rows = _load_override_rows(overrides_source) if overrides_source.exists() else []

    sorted_rules = [rule_map[key] for key in sorted(rule_map)]
    sorted_overrides = sorted(
        override_rows,
        key=lambda row: (row['state_code'], row['violation_code'], row['vehicle_class']),
    )

    BACKEND_CHALLAN_DIR.mkdir(parents=True, exist_ok=True)
    FRONTEND_OFFLINE_DIR.mkdir(parents=True, exist_ok=True)
    _write_csv(BACKEND_CHALLAN_DIR / 'violations.csv', RULE_COLUMNS, sorted_rules)
    _write_csv(BACKEND_CHALLAN_DIR / 'state_overrides.csv', OVERRIDE_COLUMNS, sorted_overrides)
    _write_csv(FRONTEND_OFFLINE_DIR / 'violations.csv', RULE_COLUMNS, sorted_rules)
    _write_csv(FRONTEND_OFFLINE_DIR / 'state_overrides.csv', OVERRIDE_COLUMNS, sorted_overrides)
    print(f'Challan assets synced: rules={len(sorted_rules)} overrides={len(sorted_overrides)}')


def sync_first_aid_bundle() -> None:
    """Always sync first-aid.json from frontend (canonical 20-article source) to chatbot data.

    The chatbot_service/data/first_aid.json was historically only 4 entries.
    The frontend/public/offline-data/first-aid.json contains the full 20 WHO-based articles
    and is the ground truth. This function overwrites unconditionally so the chatbot is never
    left with the stale 4-entry version.
    """
    source = FRONTEND_OFFLINE_DIR / 'first-aid.json'
    target = CHATBOT_DATA_DIR / 'first_aid.json'
    if not source.exists():
        print(f'WARNING: first-aid.json source not found at {source} — skipping sync')
        return
    shutil.copyfile(source, target)
    print(f'Synced first aid bundle ({source.stat().st_size:,} bytes) -> {target}')


def build_emergency_geojson() -> None:
    catalog = load_local_emergency_catalog(PROJECT_ROOT)
    features = []
    for entry in catalog:
        city, distance = _nearest_city(entry.lat, entry.lon)
        if city is None or distance > CITY_RADIUS_METERS:
            continue
        features.append(
            {
                'type': 'Feature',
                'id': entry.id,
                'geometry': {'type': 'Point', 'coordinates': [entry.lon, entry.lat]},
                'properties': {
                    'city': city.title(),
                    'name': entry.name,
                    'category': entry.category,
                    'sub_category': entry.sub_category,
                    'phone': entry.phone,
                    'phone_emergency': entry.phone_emergency,
                    'address': entry.address,
                    'has_trauma': entry.has_trauma,
                    'has_icu': entry.has_icu,
                    'is_24hr': entry.is_24hr,
                    'source': entry.source,
                },
            }
        )

    payload = {
        'type': 'FeatureCollection',
        'properties': {
            'generated_from': 'chatbot_service/data local CSV catalog',
            'feature_count': len(features),
            'cities': [city.title() for city in OFFLINE_CITY_CENTERS],
        },
        'features': features,
    }
    output_path = FRONTEND_OFFLINE_DIR / 'india-emergency.geojson'
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Emergency GeoJSON written: features={len(features)} path={output_path}')


def export_pmgsy_geojson() -> None:
    source = ROADS_DIR / 'pmgsy-geosadak-master.zip'
    target = ROADS_DIR / 'pmgsy_roads.geojson'
    if not source.exists():
        print('PMGSY archive not found; skipping pmgsy_roads.geojson export')
        return

    planned_states: list[str] = []
    skipped_archives: list[str] = []
    feature_count = 0

    with zipfile.ZipFile(source) as outer, target.open('w', encoding='utf-8') as handle:
        planned_states = _list_pmgsy_state_members(outer)
        skipped_archives = _list_pmgsy_split_archives(outer)
        properties = {
            'generated_from': source.name,
            'geometry_generalization': f'max {PMGSY_MAX_POINTS_PER_SEGMENT} points per segment',
            'planned_states': planned_states,
            'skipped_archives': skipped_archives,
        }
        handle.write('{"type":"FeatureCollection","properties":')
        json.dump(properties, handle, ensure_ascii=False, separators=(',', ':'))
        handle.write(',"features":[')

        is_first_feature = True
        exported_states: list[str] = []
        for state_name, archive_bytes in _iter_pmgsy_state_archives(outer):
            try:
                shp_bytes, dbf_bytes = _read_shapefile_bundle(archive_bytes)
            except ValueError:
                continue

            exported_states.append(state_name)
            for row, geometry in zip(_iter_dbf_rows(dbf_bytes), _iter_polyline_geometries(shp_bytes)):
                if geometry is None:
                    continue
                feature = {
                    'type': 'Feature',
                    'id': f'pmgsy-{state_name}-{row.get("ER_ID") or feature_count + 1}',
                    'geometry': geometry,
                    'properties': _build_pmgsy_properties(row, state_name),
                }
                if not is_first_feature:
                    handle.write(',')
                json.dump(feature, handle, ensure_ascii=False, separators=(',', ':'))
                is_first_feature = False
                feature_count += 1

        handle.write(']}')

    print(
        'PMGSY GeoJSON exported: '
        f'rows={feature_count} states={len(exported_states)} skipped={len(skipped_archives)} path={target}'
    )


def export_national_highways_csv() -> None:
    target = ROADS_DIR / 'national_highways.csv'
    if target.exists() and target.stat().st_size > 0:
        print(f'National highways CSV already present: {target}')
        return

    candidates = sorted(
        path for path in ROADS_DIR.glob('*.csv')
        if path.name != target.name and any(token in path.stem.lower() for token in ('nh', 'highway', 'nhai'))
    )
    if not candidates:
        summary_rows = _build_road_summary_rows()
        if not summary_rows:
            print('No usable local road CSVs found; skipping national_highways.csv export')
            return

        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    'source_file',
                    'geography_level',
                    'geography_name',
                    'period',
                    'metric_name',
                    'value',
                    'unit',
                    'notes',
                ],
            )
            writer.writeheader()
            writer.writerows(summary_rows)
        print(
            'National highways CSV synthesized from local road tables: '
            f'rows={len(summary_rows)} path={target}'
        )
        return

    shutil.copyfile(candidates[0], target)
    print(f'National highways CSV copied from {candidates[0].name} to {target}')


def _nearest_city(lat: float, lon: float) -> tuple[str | None, float]:
    best_city = None
    best_distance = float('inf')
    for city, (city_lat, city_lon) in OFFLINE_CITY_CENTERS.items():
        distance = _distance_meters(lat, lon, city_lat, city_lon)
        if distance < best_distance:
            best_city = city
            best_distance = distance
    return best_city, best_distance


def _distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _list_pmgsy_state_members(outer: zipfile.ZipFile) -> list[str]:
    return [
        Path(member).stem
        for member in sorted(name for name in outer.namelist() if '/Road_DRRP/' in name and name.endswith('.zip'))
        if not member.endswith('-split.zip')
    ]


def _list_pmgsy_split_archives(outer: zipfile.ZipFile) -> list[str]:
    return [
        Path(member).stem
        for member in sorted(name for name in outer.namelist() if '/Road_DRRP/' in name and name.endswith('-split.zip'))
    ]


def _iter_pmgsy_state_archives(outer: zipfile.ZipFile):
    for member in sorted(name for name in outer.namelist() if '/Road_DRRP/' in name and name.endswith('.zip')):
        if member.endswith('-split.zip'):
            continue
        yield Path(member).stem, outer.read(member)


def _read_shapefile_bundle(archive_bytes: bytes) -> tuple[bytes, bytes]:
    with zipfile.ZipFile(BytesIO(archive_bytes)) as archive:
        shp_names = [name for name in archive.namelist() if name.lower().endswith('.shp')]
        dbf_names = [name for name in archive.namelist() if name.lower().endswith('.dbf')]
        if not shp_names or not dbf_names:
            raise ValueError('Missing shapefile members')
        return archive.read(shp_names[0]), archive.read(dbf_names[0])


def _iter_dbf_rows(dbf_bytes: bytes) -> list[dict[str, object]]:
    header_length = struct.unpack('<H', dbf_bytes[8:10])[0]
    record_length = struct.unpack('<H', dbf_bytes[10:12])[0]
    field_specs = []
    pos = 32
    offset = 1
    while pos < header_length - 1:
        field = dbf_bytes[pos:pos + 32]
        if field[0] == 0x0D:
            break
        field_specs.append(
            (
                field[:11].split(b'\x00', 1)[0].decode('ascii', 'ignore'),
                chr(field[11]),
                field[16],
                field[17],
                offset,
            )
        )
        offset += field[16]
        pos += 32

    records = struct.unpack('<I', dbf_bytes[4:8])[0]
    row_start = header_length
    for _ in range(records):
        record = dbf_bytes[row_start:row_start + record_length]
        row_start += record_length
        if not record or record[0:1] == b'*':
            continue
        row: dict[str, object] = {}
        for name, field_type, field_len, decimals, value_offset in field_specs:
            raw = record[value_offset:value_offset + field_len]
            text = raw.decode('latin1', 'ignore').strip()
            if not text:
                continue
            if field_type == 'N':
                if decimals:
                    try:
                        row[name] = float(text)
                    except ValueError:
                        row[name] = text
                else:
                    try:
                        row[name] = int(text)
                    except ValueError:
                        row[name] = text
            else:
                row[name] = text
        yield row


def _iter_polyline_geometries(shp_bytes: bytes) -> list[dict[str, object] | None]:
    pos = 100
    total_size = len(shp_bytes)
    while pos + 8 <= total_size:
        content_length_words = struct.unpack('>i', shp_bytes[pos + 4:pos + 8])[0]
        record_end = pos + 8 + content_length_words * 2
        record = shp_bytes[pos + 8:record_end]
        pos = record_end
        if len(record) < 44:
            yield None
            continue

        shape_type = struct.unpack('<i', record[:4])[0]
        if shape_type == 0:
            yield None
            continue
        if shape_type not in {3, 13, 23}:
            yield None
            continue

        num_parts = struct.unpack('<i', record[36:40])[0]
        num_points = struct.unpack('<i', record[40:44])[0]
        parts_offset = 44
        points_offset = parts_offset + 4 * num_parts
        parts = [
            struct.unpack('<i', record[parts_offset + index * 4:parts_offset + (index + 1) * 4])[0]
            for index in range(num_parts)
        ]
        points = [
            struct.unpack('<2d', record[points_offset + index * 16:points_offset + (index + 1) * 16])
            for index in range(num_points)
        ]

        coordinates = []
        for index, start in enumerate(parts):
            end = parts[index + 1] if index + 1 < len(parts) else len(points)
            line = _downsample_line(points[start:end], max_points=PMGSY_MAX_POINTS_PER_SEGMENT)
            if len(line) < 2:
                continue
            coordinates.append([[round(lon, 6), round(lat, 6)] for lon, lat in line])

        if not coordinates:
            yield None
        elif len(coordinates) == 1:
            yield {'type': 'LineString', 'coordinates': coordinates[0]}
        else:
            yield {'type': 'MultiLineString', 'coordinates': coordinates}


def _downsample_line(points: list[tuple[float, float]], *, max_points: int) -> list[tuple[float, float]]:
    if len(points) <= max_points:
        return points
    last_index = len(points) - 1
    indexes = {
        0,
        last_index,
        *(
            min(last_index, round(step * last_index / (max_points - 1)))
            for step in range(1, max_points - 1)
        ),
    }
    return [points[index] for index in sorted(indexes)]


def _build_pmgsy_properties(row: dict[str, object], state_name: str) -> dict[str, object]:
    props: dict[str, object] = {'pmgsy_state': state_name}
    field_map = {
        'ER_ID': 'er_id',
        'STATE_ID': 'state_id',
        'BLOCK_ID': 'block_id',
        'DISTRICT_I': 'district_id',
        'DRRP_ROAD_': 'road_code',
        'RoadCatego': 'road_category',
        'RoadName': 'road_name',
        'RoadOwner': 'road_owner',
    }
    for source_key, target_key in field_map.items():
        value = row.get(source_key)
        if value not in (None, ''):
            props[target_key] = value
    return props


def _build_road_summary_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(ROADS_DIR.glob('*.csv')):
        if path.name in {'national_highways.csv', 'tolls-with-metadata.csv'}:
            continue
        if path.name.endswith('-metadata-hotosm_ind_roads_lines_geojson-zip.csv'):
            continue
        rows.extend(_normalize_road_summary_table(path))
    return rows


def _normalize_road_summary_table(path: Path) -> list[dict[str, str]]:
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return []

        geography_column = _detect_geography_column(reader.fieldnames)
        serial_columns = {'Sr. No.', 'Sl. No.', 'Sl.No.', 'S.No.', 'S. No.'}
        notes = (
            'Generated from local road programme CSVs because no direct NHAI/NH master CSV '
            'was present in chatbot_service/data/roads.'
        )
        rows: list[dict[str, str]] = []
        for raw in reader:
            geography_name = (raw.get(geography_column) or '').strip() if geography_column else ''
            if not geography_name:
                continue
            for column, value in raw.items():
                if column in serial_columns or column == geography_column:
                    continue
                metric_value = _normalize_metric_value(value or '')
                if metric_value is None:
                    continue
                metric_name, period = _split_metric_column(column)
                rows.append(
                    {
                        'source_file': path.name,
                        'geography_level': 'district' if geography_column == 'District Name' else 'state',
                        'geography_name': geography_name,
                        'period': period,
                        'metric_name': metric_name,
                        'value': metric_value,
                        'unit': 'km_or_count',
                        'notes': notes,
                    }
                )
        return rows


def _detect_geography_column(fieldnames: list[str]) -> str | None:
    candidates = ['District Name', 'State/UT', 'State', 'District', 'State/UT ']
    for candidate in candidates:
        if candidate in fieldnames:
            return candidate
    return None


def _normalize_metric_value(value: str) -> str | None:
    cleaned = value.strip()
    if not cleaned or cleaned.upper() in {'NA', 'N/A', '-'}:
        return None
    try:
        return str(int(cleaned))
    except ValueError:
        try:
            return str(float(cleaned))
        except ValueError:
            return None


def _split_metric_column(column: str) -> tuple[str, str]:
    cleaned = column.strip()
    period_match = None
    for token in ('2024-25', '2023-24', '2022-23', '2021-22', '2020-21', '2019-20'):
        if token in cleaned:
            period_match = token
            break
    if period_match is None:
        return cleaned, ''

    metric_name = cleaned.replace(period_match, '').replace(' - ', ' ').replace('(as on 14.07.2022)', '').strip()
    metric_name = ' '.join(metric_name.split()) or cleaned
    return metric_name, period_match


def main() -> None:
    parser = argparse.ArgumentParser(description='Build app-facing assets from chatbot_service/data local datasets.')
    parser.add_argument('--skip-pmgsy', action='store_true', help='Skip extracting PMGSY shapefiles into GeoJSON.')
    args = parser.parse_args()

    sync_challan_assets()
    sync_first_aid_bundle()
    build_emergency_geojson()
    export_national_highways_csv()
    if not args.skip_pmgsy:
        export_pmgsy_geojson()


if __name__ == '__main__':
    main()
