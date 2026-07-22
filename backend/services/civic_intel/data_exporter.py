# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Civic Intelligence Data Exporter — dumps PostGIS tables to CSV/JSON/GeoJSON for HuggingFace Hub."""

from __future__ import annotations

import csv
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.admin_boundary import AdminBoundary
from models.etl_run_log import ETLRunLog
from models.gov_dataset import GovDataset
from models.grievance import Grievance
from models.lgd_entity import LGDEntity
from models.municipal_feature import MunicipalFeature
from models.municipality import Municipality
from models.osm_civic_feature import OSMCivicFeature

logger = logging.getLogger(__name__)

# Default export directory
DEFAULT_EXPORT_DIR = Path(__file__).resolve().parents[1] / 'data' / 'civic_intel'


class CivicDataExporter:
    """Enterprise data exporter — dumps all civic intelligence tables to
    CSV/JSON/GeoJSON files for HuggingFace Hub upload, offline demo, and open data sharing.

    Output structure:
        data/civic_intel/
        ├── lgd_entities.csv              # 7+ lakh admin hierarchy rows
        ├── lgd_hierarchy.json            # Nested state→district→block tree
        ├── admin_boundaries.geojson      # PostGIS polygons as GeoJSON FeatureCollection
        ├── osm_civic_features.csv        # Streetlights, signals, bus stops etc.
        ├── osm_civic_features.geojson    # Same as above but GeoJSON for map rendering
        ├── gov_datasets.csv              # Data.gov.in road safety records
        ├── grievances.csv                # CPGRAMS + state PGRS grievances
        ├── municipal_features.geojson    # Municipal GIS layers
        ├── municipalities.json           # MeraWard directory (85+ corps)
        ├── etl_run_log.csv               # Pipeline audit trail
        └── _manifest.json                # Export metadata + checksums
    """

    def __init__(self, export_dir: Path | None = None):
        self.export_dir = export_dir or DEFAULT_EXPORT_DIR
        self.export_dir.mkdir(parents=True, exist_ok=True)

    async def export_all(self, db: AsyncSession) -> dict[str, Any]:
        """Export ALL civic intelligence tables. Returns manifest."""
        logger.info('[Export] Starting full civic data export to %s', self.export_dir)
        manifest: dict[str, Any] = {
            'exported_at': datetime.now(UTC).isoformat(),
            'version': '1.0.0',
            'project': 'SafeVixAI',
            'description': 'Pan-India civic intelligence dataset for road safety',
            'license': 'CC-BY-SA-4.0',
            'files': {},
        }

        exporters = [
            ('lgd_entities.csv', self._export_lgd_csv),
            ('lgd_hierarchy.json', self._export_lgd_hierarchy),
            ('admin_boundaries.geojson', self._export_boundaries_geojson),
            ('osm_civic_features.csv', self._export_osm_csv),
            ('osm_civic_features.geojson', self._export_osm_geojson),
            ('gov_datasets.csv', self._export_gov_datasets_csv),
            ('grievances.csv', self._export_grievances_csv),
            ('municipal_features.geojson', self._export_municipal_geojson),
            ('municipalities.json', self._export_municipalities_json),
            ('etl_run_log.csv', self._export_etl_log_csv),
        ]

        for filename, exporter_fn in exporters:
            try:
                count = await exporter_fn(db)
                file_path = self.export_dir / filename
                size_bytes = file_path.stat().st_size if file_path.exists() else 0
                manifest['files'][filename] = {
                    'records': count,
                    'size_bytes': size_bytes,
                    'size_human': self._human_size(size_bytes),
                }
                logger.info('[Export] %s: %d records (%s)', filename, count, self._human_size(size_bytes))
            except Exception as exc:
                manifest['files'][filename] = {'error': str(exc)}
                logger.warning('[Export] %s failed: %s', filename, exc)

        # Write manifest
        manifest_path = self.export_dir / '_manifest.json'
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        logger.info('[Export] Complete. Manifest: %s', manifest_path)
        return manifest

    # ──────────────────────────────────────────────────────────
    # LGD Entities
    # ──────────────────────────────────────────────────────────

    async def _export_lgd_csv(self, db: AsyncSession) -> int:
        """Export LGD entities to CSV."""
        result = await db.execute(
            select(LGDEntity).order_by(LGDEntity.state_code, LGDEntity.entity_type, LGDEntity.lgd_code)
        )
        entities = result.scalars().all()

        filepath = self.export_dir / 'lgd_entities.csv'
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'lgd_code', 'entity_type', 'name_en', 'name_local',
                'parent_lgd_code', 'state_code', 'census_code_2011',
                'population_census_2011', 'is_active',
            ])
            for e in entities:
                writer.writerow([
                    e.lgd_code, e.entity_type, e.name_en, e.name_local or '',
                    e.parent_lgd_code or '', e.state_code, e.census_code_2011 or '',
                    e.population_census_2011 or '', e.is_active,
                ])
        return len(entities)

    async def _export_lgd_hierarchy(self, db: AsyncSession) -> int:
        """Export LGD as nested JSON hierarchy — state → district → subdistrict → block."""
        result = await db.execute(
            select(LGDEntity).where(LGDEntity.is_active.is_(True))
            .order_by(LGDEntity.state_code, LGDEntity.entity_type)
        )
        entities = result.scalars().all()

        # Build lookup
        by_code: dict[int, dict] = {}
        for e in entities:
            by_code[e.lgd_code] = {
                'lgd_code': e.lgd_code,
                'name': e.name_en,
                'name_local': e.name_local,
                'type': e.entity_type,
                'children': [],
            }

        # Link parent→child
        roots: list[dict] = []
        for e in entities:
            node = by_code[e.lgd_code]
            if e.parent_lgd_code and e.parent_lgd_code in by_code:
                by_code[e.parent_lgd_code]['children'].append(node)
            elif e.entity_type == 'state':
                roots.append(node)

        hierarchy = {
            'type': 'lgd_hierarchy',
            'total_entities': len(entities),
            'states': roots,
        }

        filepath = self.export_dir / 'lgd_hierarchy.json'
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(hierarchy, f, indent=2, ensure_ascii=False)
        return len(entities)

    # ──────────────────────────────────────────────────────────
    # Admin Boundaries
    # ──────────────────────────────────────────────────────────

    async def _export_boundaries_geojson(self, db: AsyncSession) -> int:
        """Export admin boundaries as GeoJSON FeatureCollection."""
        result = await db.execute(
            select(
                AdminBoundary.id, AdminBoundary.level, AdminBoundary.code,
                AdminBoundary.name, AdminBoundary.state_code,
                AdminBoundary.area_sqkm, AdminBoundary.centroid_lat,
                AdminBoundary.centroid_lon, AdminBoundary.source,
                func.ST_AsGeoJSON(AdminBoundary.boundary).label('geojson'),
            ).order_by(AdminBoundary.level, AdminBoundary.state_code)
        )
        rows = result.all()

        features = []
        for r in rows:
            features.append({
                'type': 'Feature',
                'properties': {
                    'id': r.id, 'level': r.level, 'code': r.code,
                    'name': r.name, 'state_code': r.state_code,
                    'area_sqkm': r.area_sqkm, 'source': r.source,
                    'centroid': [r.centroid_lon, r.centroid_lat] if r.centroid_lat else None,
                },
                'geometry': json.loads(r.geojson) if r.geojson else None,
            })

        fc = {'type': 'FeatureCollection', 'features': features}
        filepath = self.export_dir / 'admin_boundaries.geojson'
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(fc, f, ensure_ascii=False)
        return len(features)

    # ──────────────────────────────────────────────────────────
    # OSM Civic Features
    # ──────────────────────────────────────────────────────────

    async def _export_osm_csv(self, db: AsyncSession) -> int:
        """Export OSM civic features to CSV."""
        result = await db.execute(
            select(
                OSMCivicFeature.osm_id, OSMCivicFeature.feature_type,
                OSMCivicFeature.city, OSMCivicFeature.district_code,
                func.ST_Y(OSMCivicFeature.location).label('lat'),
                func.ST_X(OSMCivicFeature.location).label('lon'),
                OSMCivicFeature.tags_json, OSMCivicFeature.created_at,
            ).order_by(OSMCivicFeature.city, OSMCivicFeature.feature_type)
        )
        rows = result.all()

        filepath = self.export_dir / 'osm_civic_features.csv'
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'osm_id', 'feature_type', 'city', 'district_code',
                'latitude', 'longitude', 'tags', 'created_at',
            ])
            for r in rows:
                writer.writerow([
                    r.osm_id, r.feature_type, r.city or '', r.district_code or '',
                    r.lat, r.lon, json.dumps(r.tags_json, ensure_ascii=False),
                    r.created_at.isoformat() if r.created_at else '',
                ])
        return len(rows)

    async def _export_osm_geojson(self, db: AsyncSession) -> int:
        """Export OSM civic features as GeoJSON."""
        result = await db.execute(
            select(
                OSMCivicFeature.osm_id, OSMCivicFeature.feature_type,
                OSMCivicFeature.city, OSMCivicFeature.tags_json,
                func.ST_AsGeoJSON(OSMCivicFeature.location).label('geojson'),
            )
        )
        rows = result.all()

        features = []
        for r in rows:
            features.append({
                'type': 'Feature',
                'properties': {
                    'osm_id': r.osm_id, 'feature_type': r.feature_type,
                    'city': r.city, 'tags': r.tags_json,
                },
                'geometry': json.loads(r.geojson) if r.geojson else None,
            })

        fc = {'type': 'FeatureCollection', 'features': features}
        filepath = self.export_dir / 'osm_civic_features.geojson'
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(fc, f, ensure_ascii=False)
        return len(features)

    # ──────────────────────────────────────────────────────────
    # Data.gov.in Datasets
    # ──────────────────────────────────────────────────────────

    async def _export_gov_datasets_csv(self, db: AsyncSession) -> int:
        """Export gov datasets to CSV."""
        result = await db.execute(
            select(GovDataset).order_by(GovDataset.dataset_slug, GovDataset.year)
        )
        records = result.scalars().all()

        filepath = self.export_dir / 'gov_datasets.csv'
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'dataset_slug', 'resource_id', 'year', 'state_code',
                'district_name', 'metric_name', 'metric_value', 'unit', 'data_json',
            ])
            for r in records:
                writer.writerow([
                    r.dataset_slug, r.resource_id, r.year or '', r.state_code or '',
                    r.district_name or '', r.metric_name or '', r.metric_value or '',
                    r.unit or '', json.dumps(r.data_json, ensure_ascii=False),
                ])
        return len(records)

    # ──────────────────────────────────────────────────────────
    # Grievances
    # ──────────────────────────────────────────────────────────

    async def _export_grievances_csv(self, db: AsyncSession) -> int:
        """Export grievances to CSV."""
        result = await db.execute(
            select(
                Grievance.grievance_ref, Grievance.source, Grievance.category,
                Grievance.subcategory, Grievance.description,
                Grievance.complainant_district, Grievance.state_code,
                Grievance.status, Grievance.filed_at, Grievance.resolved_at,
                Grievance.ministry,
                func.ST_Y(Grievance.location).label('lat'),
                func.ST_X(Grievance.location).label('lon'),
            ).order_by(Grievance.source, Grievance.created_at.desc())
        )
        rows = result.all()

        filepath = self.export_dir / 'grievances.csv'
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'grievance_ref', 'source', 'category', 'subcategory',
                'description', 'district', 'state_code', 'status',
                'filed_at', 'resolved_at', 'ministry', 'latitude', 'longitude',
            ])
            for r in rows:
                writer.writerow([
                    r.grievance_ref, r.source, r.category, r.subcategory or '',
                    r.description[:500], r.complainant_district or '', r.state_code or '',
                    r.status, r.filed_at.isoformat() if r.filed_at else '',
                    r.resolved_at.isoformat() if r.resolved_at else '',
                    r.ministry or '', r.lat or '', r.lon or '',
                ])
        return len(rows)

    # ──────────────────────────────────────────────────────────
    # Municipal Features
    # ──────────────────────────────────────────────────────────

    async def _export_municipal_geojson(self, db: AsyncSession) -> int:
        """Export municipal features as GeoJSON."""
        result = await db.execute(
            select(
                MunicipalFeature.municipality, MunicipalFeature.layer_name,
                MunicipalFeature.feature_id, MunicipalFeature.attributes_json,
                func.ST_AsGeoJSON(MunicipalFeature.geometry).label('geojson'),
            ).order_by(MunicipalFeature.municipality, MunicipalFeature.layer_name)
        )
        rows = result.all()

        features = []
        for r in rows:
            features.append({
                'type': 'Feature',
                'properties': {
                    'municipality': r.municipality, 'layer': r.layer_name,
                    'feature_id': r.feature_id, **r.attributes_json,
                },
                'geometry': json.loads(r.geojson) if r.geojson else None,
            })

        fc = {'type': 'FeatureCollection', 'features': features}
        filepath = self.export_dir / 'municipal_features.geojson'
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(fc, f, ensure_ascii=False)
        return len(features)

    # ──────────────────────────────────────────────────────────
    # Municipalities
    # ──────────────────────────────────────────────────────────

    async def _export_municipalities_json(self, db: AsyncSession) -> int:
        """Export municipality directory as JSON."""
        result = await db.execute(
            select(Municipality).where(Municipality.is_active.is_(True))
            .order_by(Municipality.state_code, Municipality.name)
        )
        municipalities = result.scalars().all()

        data = []
        for m in municipalities:
            data.append({
                'slug': m.slug, 'name': m.name, 'short_name': m.short_name,
                'municipality_type': m.municipality_type,
                'city': m.city, 'state_code': m.state_code, 'state_name': m.state_name,
                'lgd_code': m.lgd_code, 'district_name': m.district_name,
                'contact': {
                    'headquarters_address': m.headquarters_address,
                    'helpline_phone': m.helpline_phone,
                    'whatsapp_number': m.whatsapp_number,
                    'email': m.email, 'website_url': m.website_url,
                    'app_name': m.app_name, 'app_url': m.app_url,
                    'grievance_portal_url': m.grievance_portal_url,
                },
                'leadership': {
                    'mayor_name': m.mayor_name,
                    'commissioner_name': m.commissioner_name,
                },
                'stats': {
                    'ward_count': m.ward_count, 'population': m.population,
                    'area_sqkm': m.area_sqkm,
                },
                'geo': {
                    'centroid_lat': m.centroid_lat, 'centroid_lon': m.centroid_lon,
                },
                'description': m.description,
                'services_offered': m.services_offered,
            })

        output = {
            'type': 'municipality_directory',
            'count': len(data),
            'exported_at': datetime.now(UTC).isoformat(),
            'municipalities': data,
        }

        filepath = self.export_dir / 'municipalities.json'
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        return len(data)

    # ──────────────────────────────────────────────────────────
    # ETL Run Log
    # ──────────────────────────────────────────────────────────

    async def _export_etl_log_csv(self, db: AsyncSession) -> int:
        """Export ETL audit trail to CSV."""
        result = await db.execute(
            select(ETLRunLog).order_by(ETLRunLog.started_at.desc())
        )
        logs = result.scalars().all()

        filepath = self.export_dir / 'etl_run_log.csv'
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'id', 'pipeline_name', 'started_at', 'finished_at', 'status',
                'records_fetched', 'records_inserted', 'records_updated',
                'records_skipped', 'error_message',
            ])
            for l in logs:
                writer.writerow([
                    l.id, l.pipeline_name,
                    l.started_at.isoformat() if l.started_at else '',
                    l.finished_at.isoformat() if l.finished_at else '',
                    l.status, l.records_fetched, l.records_inserted,
                    l.records_updated, l.records_skipped,
                    l.error_message or '',
                ])
        return len(logs)

    # ──────────────────────────────────────────────────────────
    # Utilities
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _human_size(size_bytes: int) -> str:
        """Convert bytes to human-readable string."""
        for unit in ('B', 'KB', 'MB', 'GB'):
            if abs(size_bytes) < 1024:
                return f'{size_bytes:.1f} {unit}'
            size_bytes /= 1024
        return f'{size_bytes:.1f} TB'
