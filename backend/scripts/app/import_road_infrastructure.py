# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import argparse
import asyncio
import csv
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from geoalchemy2.elements import WKTElement
from shapely.geometry import LineString, MultiLineString, shape
from shapely.ops import linemerge
from shapely.wkt import loads as load_wkt
from sqlalchemy.dialects.postgresql import insert

from core.database import AsyncSessionLocal
from models.road_issue import RoadInfrastructure

FIELD_ALIASES = {
    'road_id': ['road_id', 'id', 'segment_id', 'project_id', 'road_code'],
    'road_name': ['road_name', 'name', 'road', 'street_name'],
    'road_type': ['road_type', 'type', 'category', 'highway_type'],
    'road_number': ['road_number', 'ref', 'road_ref', 'highway_no'],
    'length_km': ['length_km', 'length', 'road_length_km'],
    'state_code': ['state_code', 'state', 'state_abbr'],
    'contractor_name': ['contractor_name', 'contractor', 'agency_name'],
    'exec_engineer': ['exec_engineer', 'executive_engineer', 'engineer_name'],
    'exec_engineer_phone': ['exec_engineer_phone', 'engineer_phone', 'contact_phone'],
    'budget_sanctioned': ['budget_sanctioned', 'sanctioned_budget', 'budget'],
    'budget_spent': ['budget_spent', 'spent_budget', 'expenditure'],
    'construction_date': ['construction_date', 'built_on', 'start_date'],
    'last_relayed_date': ['last_relayed_date', 'last_relaid_date', 'last_maintenance_date'],
    'next_maintenance': ['next_maintenance', 'maintenance_due', 'next_service_date'],
    'project_source': ['project_source', 'source_name', 'dataset'],
    'data_source_url': ['data_source_url', 'source_url', 'portal_url'],
    'geometry': ['geometry', 'geometry_wkt', 'wkt', 'line_wkt'],
}


@dataclass(slots=True)
class InfrastructureRecord:
    road_id: str
    geometry_wkt: str
    road_name: str | None = None
    road_type: str | None = None
    road_number: str | None = None
    length_km: float | None = None
    state_code: str | None = None
    contractor_name: str | None = None
    exec_engineer: str | None = None
    exec_engineer_phone: str | None = None
    budget_sanctioned: int | None = None
    budget_spent: int | None = None
    construction_date: date | None = None
    last_relayed_date: date | None = None
    next_maintenance: date | None = None
    project_source: str | None = None
    data_source_url: str | None = None

    def to_row(self) -> dict[str, Any]:
        return {
            'road_id': self.road_id,
            'road_name': self.road_name,
            'road_type': self.road_type,
            'road_number': self.road_number,
            'length_km': self.length_km,
            'geometry': WKTElement(self.geometry_wkt, srid=4326),
            'state_code': self.state_code,
            'contractor_name': self.contractor_name,
            'exec_engineer': self.exec_engineer,
            'exec_engineer_phone': self.exec_engineer_phone,
            'budget_sanctioned': self.budget_sanctioned,
            'budget_spent': self.budget_spent,
            'construction_date': self.construction_date,
            'last_relayed_date': self.last_relayed_date,
            'next_maintenance': self.next_maintenance,
            'project_source': self.project_source,
            'data_source_url': self.data_source_url,
        }


def _pick_value(source: dict[str, Any], field_name: str) -> Any:
    for alias in FIELD_ALIASES[field_name]:
        if alias in source and source[alias] not in (None, ''):
            return source[alias]
    return None


def _parse_number(value: Any) -> int | None:
    if value in (None, ''):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    cleaned = str(value).replace(',', '').strip()
    if not cleaned:
        return None
    return int(float(cleaned))


def _parse_float(value: Any) -> float | None:
    if value in (None, ''):
        return None
    return float(str(value).replace(',', '').strip())


def _parse_date(value: Any) -> date | None:
    if value in (None, ''):
        return None
    return date.fromisoformat(str(value).strip())


def _coerce_linestring(geometry_payload: Any) -> str:
    if geometry_payload is None:
        raise ValueError('Missing geometry')
    if isinstance(geometry_payload, str):
        geom = load_wkt(geometry_payload)
    else:
        geom = shape(geometry_payload)

    if isinstance(geom, LineString):
        return geom.wkt
    if isinstance(geom, MultiLineString):
        merged = linemerge(geom)
        if isinstance(merged, LineString):
            return merged.wkt
    raise ValueError('Only LineString or mergeable MultiLineString geometries are supported')


def _normalize_record(
    source: dict[str, Any],
    *,
    default_state_code: str | None,
    default_project_source: str | None,
    default_data_source_url: str | None,
    index: int,
) -> InfrastructureRecord:
    road_id = _pick_value(source, 'road_id')
    if not road_id:
        road_id = f'road-segment-{index}'
    geometry_value = _pick_value(source, 'geometry')
    geometry_wkt = _coerce_linestring(geometry_value)
    return InfrastructureRecord(
        road_id=str(road_id),
        geometry_wkt=geometry_wkt,
        road_name=_pick_value(source, 'road_name'),
        road_type=_pick_value(source, 'road_type'),
        road_number=_pick_value(source, 'road_number'),
        length_km=_parse_float(_pick_value(source, 'length_km')),
        state_code=str(_pick_value(source, 'state_code') or default_state_code or '').upper() or None,
        contractor_name=_pick_value(source, 'contractor_name'),
        exec_engineer=_pick_value(source, 'exec_engineer'),
        exec_engineer_phone=_pick_value(source, 'exec_engineer_phone'),
        budget_sanctioned=_parse_number(_pick_value(source, 'budget_sanctioned')),
        budget_spent=_parse_number(_pick_value(source, 'budget_spent')),
        construction_date=_parse_date(_pick_value(source, 'construction_date')),
        last_relayed_date=_parse_date(_pick_value(source, 'last_relayed_date')),
        next_maintenance=_parse_date(_pick_value(source, 'next_maintenance')),
        project_source=_pick_value(source, 'project_source') or default_project_source,
        data_source_url=_pick_value(source, 'data_source_url') or default_data_source_url,
    )


def _read_json_payload(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(payload, dict) and payload.get('type') == 'FeatureCollection':
        records = []
        for feature in payload.get('features', []):
            properties = feature.get('properties', {}).copy()
            properties['geometry'] = feature.get('geometry')
            records.append(properties)
        return records
    if isinstance(payload, list):
        return [dict(item) for item in payload]
    if isinstance(payload, dict):
        return [payload]
    raise ValueError('Unsupported JSON payload format')


def _read_csv_payload(path: Path) -> list[dict[str, Any]]:
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _load_records(path: Path, fmt: str) -> list[dict[str, Any]]:
    if fmt == 'auto':
        suffix = path.suffix.lower()
        if suffix in {'.geojson', '.json'}:
            fmt = 'json'
        elif suffix == '.csv':
            fmt = 'csv'
        else:
            raise ValueError(f'Could not infer file format from "{path.name}"')

    if fmt == 'json':
        return _read_json_payload(path)
    if fmt == 'csv':
        return _read_csv_payload(path)
    raise ValueError(f'Unsupported format "{fmt}"')


async def import_records(
    records: list[InfrastructureRecord],
    batch_size: int = 300,
) -> int:
    rows = [record.to_row() for record in records]
    if not rows:
        return 0

    # Deduplicate by road_id WITHIN the full list (keep last occurrence).
    # This prevents PostgreSQL errors when the same road_id appears twice
    # in a single INSERT VALUES list (ON CONFLICT can't handle intra-batch dupes).
    seen: dict[str, dict] = {}
    for row in rows:
        seen[row['road_id']] = row
    rows = list(seen.values())

    total = 0
    async with AsyncSessionLocal() as session:
        for i in range(0, len(rows), batch_size):
            chunk = rows[i : i + batch_size]
            stmt = insert(RoadInfrastructure).values(chunk)
            upsert = stmt.on_conflict_do_update(
                index_elements=['road_id'],
                set_={
                    'road_name': stmt.excluded.road_name,
                    'road_type': stmt.excluded.road_type,
                    'road_number': stmt.excluded.road_number,
                    'length_km': stmt.excluded.length_km,
                    'geometry': stmt.excluded.geometry,
                    'state_code': stmt.excluded.state_code,
                    'contractor_name': stmt.excluded.contractor_name,
                    'exec_engineer': stmt.excluded.exec_engineer,
                    'exec_engineer_phone': stmt.excluded.exec_engineer_phone,
                    'budget_sanctioned': stmt.excluded.budget_sanctioned,
                    'budget_spent': stmt.excluded.budget_spent,
                    'construction_date': stmt.excluded.construction_date,
                    'last_relayed_date': stmt.excluded.last_relayed_date,
                    'next_maintenance': stmt.excluded.next_maintenance,
                    'project_source': stmt.excluded.project_source,
                    'data_source_url': stmt.excluded.data_source_url,
                },
            )
            await session.execute(upsert)
            await session.commit()
            total += len(chunk)
            print(f'  Batch {i // batch_size + 1}: {len(chunk)} rows upserted  (running total: {total})')
    return total



async def main() -> None:
    parser = argparse.ArgumentParser(
        description='Import official road infrastructure datasets from CSV/JSON/GeoJSON into road_infrastructure.',
    )
    parser.add_argument('input_path', help='Path to CSV, JSON, or GeoJSON dataset.')
    parser.add_argument('--format', choices=['auto', 'csv', 'json'], default='auto')
    parser.add_argument('--default-state-code', help='Fallback state code for rows missing one.')
    parser.add_argument('--default-project-source', help='Fallback project source label.')
    parser.add_argument('--default-data-source-url', help='Fallback source URL stored with imported rows.')
    args = parser.parse_args()

    input_path = Path(args.input_path).resolve()
    if not input_path.exists():
        raise SystemExit(f'Input file not found: {input_path}')

    raw_records = _load_records(input_path, args.format)
    records: list[InfrastructureRecord] = []
    skipped = 0

    for index, raw_record in enumerate(raw_records, start=1):
        try:
            records.append(
                _normalize_record(
                    raw_record,
                    default_state_code=args.default_state_code,
                    default_project_source=args.default_project_source,
                    default_data_source_url=args.default_data_source_url,
                    index=index,
                )
            )
        except Exception as exc:
            skipped += 1
            print(f'Skipping row {index}: {exc}')

    imported = await import_records(records)
    print(f'Imported {imported} road infrastructure rows from {input_path.name}.')
    if skipped:
        print(f'Skipped {skipped} rows because they could not be normalized.')


if __name__ == '__main__':
    asyncio.run(main())
