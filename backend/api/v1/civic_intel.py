# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Civic Intelligence API — boundaries, LGD, features, grievances, municipalities."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.limiter import limiter
from core.config import get_settings
from core.database import get_async_session
from core.rbac import require_role, Role
from models.admin_boundary import AdminBoundary
from models.etl_run_log import ETLRunLog
from models.gov_dataset import GovDataset
from models.grievance import Grievance
from models.lgd_entity import LGDEntity
from models.municipality import Municipality
from models.municipal_feature import MunicipalFeature
from models.osm_civic_feature import OSMCivicFeature

logger = logging.getLogger(__name__)

router = APIRouter(tags=['Civic Intelligence'])


# ──────────────────────────────────────────────────────────
# BOUNDARIES
# ──────────────────────────────────────────────────────────

@limiter.limit("20/minute")
@router.get('/civic/boundaries')
async def get_boundaries(request: Request, 
    level: str = Query('district', description='state, district, subdistrict, ward'),
    state_code: str | None = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Get admin boundary GeoJSON for map rendering."""
    stmt = select(
        AdminBoundary.id,
        AdminBoundary.level,
        AdminBoundary.code,
        AdminBoundary.name,
        AdminBoundary.state_code,
        AdminBoundary.area_sqkm,
        AdminBoundary.centroid_lat,
        AdminBoundary.centroid_lon,
        func.ST_AsGeoJSON(AdminBoundary.boundary).label('geojson'),
    ).where(AdminBoundary.level == level)

    if state_code:
        stmt = stmt.where(AdminBoundary.state_code == state_code.upper())

    result = await db.execute(stmt)
    rows = result.all()

    features = []
    for row in rows:
        import json
        features.append({
            'type': 'Feature',
            'properties': {
                'id': row.id,
                'code': row.code,
                'name': row.name,
                'state_code': row.state_code,
                'area_sqkm': row.area_sqkm,
            },
            'geometry': json.loads(row.geojson) if row.geojson else None,
        })

    return {'type': 'FeatureCollection', 'features': features}


@limiter.limit("20/minute")
@router.get('/civic/boundaries/contains')
async def boundary_point_lookup(request: Request, 
    lat: float = Query(..., ge=-90, le=90, description='Latitude'),
    lon: float = Query(..., ge=-180, le=180, description='Longitude'),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Find which admin boundaries contain a given point (reverse geocode)."""
    point = f'SRID=4326;POINT({lon} {lat})'
    stmt = select(
        AdminBoundary.level,
        AdminBoundary.code,
        AdminBoundary.name,
        AdminBoundary.state_code,
    ).where(
        func.ST_Contains(AdminBoundary.boundary, func.ST_GeomFromEWKT(point))
    ).order_by(AdminBoundary.level)

    result = await db.execute(stmt)
    rows = result.all()
    return {
        'lat': lat, 'lon': lon,
        'boundaries': [
            {'level': r.level, 'code': r.code, 'name': r.name, 'state_code': r.state_code}
            for r in rows
        ],
    }


# ──────────────────────────────────────────────────────────
# LGD DIRECTORY
# ──────────────────────────────────────────────────────────

@limiter.limit("20/minute")
@router.get('/civic/lgd/lookup')
async def lgd_lookup(request: Request, 
    q: str | None = Query(None, description='Search term'),
    entity_type: str | None = Query(None),
    state_code: str | None = Query(None),
    lgd_code: int | None = Query(None),
    limit: int = Query(50, le=500),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Search LGD entities by name, type, state, or code."""
    stmt = select(LGDEntity).where(LGDEntity.is_active.is_(True))

    if q:
        stmt = stmt.where(LGDEntity.name_en.ilike(f'%{q}%'))
    if entity_type:
        stmt = stmt.where(LGDEntity.entity_type == entity_type)
    if state_code:
        stmt = stmt.where(LGDEntity.state_code == state_code.upper())
    if lgd_code:
        stmt = stmt.where(LGDEntity.lgd_code == lgd_code)

    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    entities = result.scalars().all()

    return {
        'count': len(entities),
        'entities': [
            {
                'lgd_code': e.lgd_code,
                'entity_type': e.entity_type,
                'name_en': e.name_en,
                'name_local': e.name_local,
                'state_code': e.state_code,
                'parent_lgd_code': e.parent_lgd_code,
                'census_code_2011': e.census_code_2011,
                'population_census_2011': e.population_census_2011,
            }
            for e in entities
        ],
    }


@limiter.limit("20/minute")
@router.get('/civic/lgd/hierarchy')
async def lgd_hierarchy(request: Request, 
    state_code: str = Query(..., description='State code (e.g., TN, AP, MH)'),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Get full LGD hierarchy for a state — state → districts → subdistricts → blocks."""
    stmt = (
        select(LGDEntity)
        .where(LGDEntity.state_code == state_code.upper())
        .where(LGDEntity.is_active.is_(True))
        .order_by(LGDEntity.entity_type, LGDEntity.name_en)
    )
    result = await db.execute(stmt)
    entities = result.scalars().all()

    hierarchy: dict[str, list] = {}
    for e in entities:
        hierarchy.setdefault(e.entity_type, []).append({
            'lgd_code': e.lgd_code,
            'name_en': e.name_en,
            'parent_lgd_code': e.parent_lgd_code,
        })

    return {'state_code': state_code.upper(), 'hierarchy': hierarchy}


# ──────────────────────────────────────────────────────────
# OSM CIVIC FEATURES
# ──────────────────────────────────────────────────────────

@limiter.limit("20/minute")
@router.get('/civic/features/nearby')
async def get_nearby_features(request: Request, 
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius: int = Query(2000, description='Radius in meters'),
    feature_type: str | None = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Get OSM civic features within radius of a point."""
    point = func.ST_MakePoint(lon, lat)
    distance_col = func.ST_Distance(
        func.cast(OSMCivicFeature.location, text('geography')),
        func.cast(func.ST_SetSRID(point, 4326), text('geography')),
    ).label('distance_m')

    stmt = select(
        OSMCivicFeature.id,
        OSMCivicFeature.osm_id,
        OSMCivicFeature.feature_type,
        OSMCivicFeature.city,
        OSMCivicFeature.tags_json,
        func.ST_Y(OSMCivicFeature.location).label('lat'),
        func.ST_X(OSMCivicFeature.location).label('lon'),
        distance_col,
    ).where(
        func.ST_DWithin(
            func.cast(OSMCivicFeature.location, text('geography')),
            func.cast(func.ST_SetSRID(point, 4326), text('geography')),
            radius,
        )
    )

    if feature_type:
        stmt = stmt.where(OSMCivicFeature.feature_type == feature_type)

    stmt = stmt.order_by(distance_col).limit(200)
    result = await db.execute(stmt)
    rows = result.all()

    return {
        'count': len(rows),
        'features': [
            {
                'id': r.id, 'osm_id': r.osm_id, 'feature_type': r.feature_type,
                'city': r.city, 'lat': r.lat, 'lon': r.lon,
                'distance_m': round(r.distance_m, 1) if r.distance_m else None,
                'tags': r.tags_json,
            }
            for r in rows
        ],
    }


@limiter.limit("20/minute")
@router.get('/civic/features/heatmap')
async def get_feature_heatmap(request: Request, 
    feature_type: str = Query(...),
    state_code: str | None = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Get feature density data for heatmap visualization."""
    stmt = select(
        OSMCivicFeature.city,
        func.count(OSMCivicFeature.id).label('count'),
        func.avg(func.ST_Y(OSMCivicFeature.location)).label('avg_lat'),
        func.avg(func.ST_X(OSMCivicFeature.location)).label('avg_lon'),
    ).where(
        OSMCivicFeature.feature_type == feature_type
    ).group_by(OSMCivicFeature.city)

    result = await db.execute(stmt)
    rows = result.all()

    return {
        'feature_type': feature_type,
        'clusters': [
            {'city': r.city, 'count': r.count, 'lat': float(r.avg_lat), 'lon': float(r.avg_lon)}
            for r in rows if r.avg_lat
        ],
    }


# ──────────────────────────────────────────────────────────
# DATA.GOV.IN DATASETS
# ──────────────────────────────────────────────────────────

@limiter.limit("20/minute")
@router.get('/civic/datasets')
async def get_datasets(request: Request, 
    slug: str | None = Query(None),
    state_code: str | None = Query(None),
    year: int | None = Query(None),
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Query ingested Data.gov.in datasets."""
    stmt = select(GovDataset)

    if slug:
        stmt = stmt.where(GovDataset.dataset_slug == slug)
    if state_code:
        stmt = stmt.where(GovDataset.state_code == state_code.upper())
    if year:
        stmt = stmt.where(GovDataset.year == year)

    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    records = result.scalars().all()

    return {
        'count': len(records),
        'records': [
            {
                'id': r.id, 'dataset_slug': r.dataset_slug, 'year': r.year,
                'state_code': r.state_code, 'district_name': r.district_name,
                'metric_name': r.metric_name, 'metric_value': r.metric_value,
                'unit': r.unit, 'data': r.data_json,
            }
            for r in records
        ],
    }


# ──────────────────────────────────────────────────────────
# GRIEVANCES
# ──────────────────────────────────────────────────────────

@limiter.limit("20/minute")
@router.get('/civic/grievances')
async def get_grievances(request: Request, 
    source: str | None = Query(None),
    category: str | None = Query(None),
    state_code: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Query civic grievances from all portals."""
    stmt = select(Grievance)

    if source:
        stmt = stmt.where(Grievance.source == source)
    if category:
        stmt = stmt.where(Grievance.category == category)
    if state_code:
        stmt = stmt.where(Grievance.state_code == state_code.upper())
    if status:
        stmt = stmt.where(Grievance.status == status)

    stmt = stmt.order_by(Grievance.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    records = result.scalars().all()

    return {
        'count': len(records),
        'grievances': [
            {
                'id': r.id, 'source': r.source, 'grievance_ref': r.grievance_ref,
                'category': r.category, 'subcategory': r.subcategory,
                'description': r.description[:200],
                'state_code': r.state_code, 'district': r.complainant_district,
                'status': r.status,
                'filed_at': r.filed_at.isoformat() if r.filed_at else None,
                'resolved_at': r.resolved_at.isoformat() if r.resolved_at else None,
            }
            for r in records
        ],
    }


# ──────────────────────────────────────────────────────────
# COMPOSITE OVERLAY
# ──────────────────────────────────────────────────────────

@limiter.limit("20/minute")
@router.get('/civic/stats')
async def get_civic_stats(request: Request, 
    state_code: str | None = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Get aggregated civic intelligence statistics."""
    from services.civic_intel.civic_analytics_service import CivicAnalyticsService
    return await CivicAnalyticsService.get_civic_stats(db, state_code)


# ──────────────────────────────────────────────────────────
# MUNICIPALITY CIVIC HUB (MeraWard-style)
# ──────────────────────────────────────────────────────────

@limiter.limit("20/minute")
@router.get('/civic/municipalities')
async def list_municipalities(request: Request, 
    q: str | None = Query(None, description='Search by name'),
    state_code: str | None = Query(None),
    municipality_type: str | None = Query(None),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Search and list municipalities — MeraWard-style directory."""
    stmt = select(Municipality).where(Municipality.is_active.is_(True))

    if q:
        stmt = stmt.where(
            Municipality.name.ilike(f'%{q}%')
            | Municipality.city.ilike(f'%{q}%')
            | Municipality.short_name.ilike(f'%{q}%')
        )
    if state_code:
        stmt = stmt.where(Municipality.state_code == state_code.upper())
    if municipality_type:
        stmt = stmt.where(Municipality.municipality_type == municipality_type)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(Municipality.name).offset(offset).limit(limit)
    result = await db.execute(stmt)
    municipalities = result.scalars().all()

    return {
        'total': total,
        'municipalities': [
            {
                'slug': m.slug, 'name': m.name, 'short_name': m.short_name,
                'municipality_type': m.municipality_type,
                'city': m.city, 'state_code': m.state_code,
                'state_name': m.state_name, 'ward_count': m.ward_count,
                'population': m.population, 'helpline_phone': m.helpline_phone,
            }
            for m in municipalities
        ],
    }


@limiter.limit("20/minute")
@router.get('/civic/municipalities/nearby')
async def nearby_municipality(request: Request, 
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    limit: int = Query(5, le=20),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Find nearest municipalities by GPS coordinates."""
    point = func.ST_MakePoint(lon, lat)
    distance_col = func.ST_Distance(
        func.ST_MakePoint(Municipality.centroid_lon, Municipality.centroid_lat)
        .cast(text('geography')),
        func.ST_SetSRID(point, 4326).cast(text('geography')),
    ).label('distance_m')

    stmt = (
        select(Municipality, distance_col)
        .where(Municipality.is_active.is_(True))
        .where(Municipality.centroid_lat.isnot(None))
        .order_by(distance_col)
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.all()

    return {
        'lat': lat, 'lon': lon,
        'municipalities': [
            {
                'slug': m.slug, 'name': m.name, 'city': m.city,
                'state_code': m.state_code, 'distance_km': round(d / 1000, 1),
            }
            for m, d in rows
        ],
    }


@limiter.limit("20/minute")
@router.get('/civic/municipalities/{slug}')
async def get_municipality(request: Request, 
    slug: str,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Full municipality profile — MeraWard-style."""
    result = await db.execute(
        select(Municipality).where(Municipality.slug == slug)
    )
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail='Municipality not found')

    return {
        'slug': m.slug, 'name': m.name, 'short_name': m.short_name,
        'municipality_type': m.municipality_type,
        'city': m.city, 'state_code': m.state_code, 'state_name': m.state_name,
        'lgd_code': m.lgd_code, 'district_name': m.district_name,
        'contact': {
            'headquarters_address': m.headquarters_address,
            'helpline_phone': m.helpline_phone,
            'whatsapp_number': m.whatsapp_number,
            'email': m.email,
            'website_url': m.website_url,
            'app_name': m.app_name,
            'app_url': m.app_url,
            'grievance_portal_url': m.grievance_portal_url,
        },
        'leadership': {
            'mayor_name': m.mayor_name,
            'mayor_photo_url': m.mayor_photo_url,
            'commissioner_name': m.commissioner_name,
            'commissioner_phone': m.commissioner_phone,
        },
        'stats': {
            'ward_count': m.ward_count,
            'population': m.population,
            'area_sqkm': m.area_sqkm,
        },
        'geo': {
            'centroid_lat': m.centroid_lat,
            'centroid_lon': m.centroid_lon,
        },
        'description': m.description,
        'services_offered': m.services_offered,
        'last_verified': m.last_verified.isoformat() if m.last_verified else None,
    }


@limiter.limit("20/minute")
@router.get('/civic/municipalities/{slug}/stats')
async def get_municipality_stats(request: Request, 
    slug: str,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Get local complaint/grievance stats for a municipality."""
    from services.civic_intel.civic_analytics_service import CivicAnalyticsService
    return await CivicAnalyticsService.get_municipality_stats(db, slug)


@limiter.limit("20/minute")
@router.get('/civic/municipalities/{slug}/wards')
async def get_municipality_wards(request: Request, 
    slug: str,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Get ward list and boundaries for a municipality."""
    result = await db.execute(
        select(Municipality).where(Municipality.slug == slug)
    )
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail='Municipality not found')

    # Get ward boundaries from municipal_features
    ward_stmt = select(
        MunicipalFeature.feature_id,
        MunicipalFeature.attributes_json,
        func.ST_AsGeoJSON(MunicipalFeature.geometry).label('geojson'),
    ).where(
        MunicipalFeature.municipality == m.short_name,
        MunicipalFeature.layer_name.ilike('%ward%'),
    )

    ward_result = await db.execute(ward_stmt)
    wards = ward_result.all()

    import json
    features = []
    for w in wards:
        features.append({
            'type': 'Feature',
            'properties': {
                'feature_id': w.feature_id,
                **w.attributes_json,
            },
            'geometry': json.loads(w.geojson) if w.geojson else None,
        })

    return {
        'slug': slug,
        'ward_count': m.ward_count,
        'type': 'FeatureCollection',
        'features': features,
    }


# ──────────────────────────────────────────────────────────
# ADMIN ETL MANAGEMENT
# ──────────────────────────────────────────────────────────

@limiter.limit("5/minute")
@router.post('/admin/civic/ingest/{pipeline}')
async def trigger_ingest(request: Request, 
    pipeline: str,
    current_user: dict = Depends(require_role(Role.OPERATOR)),
) -> dict[str, Any]:
    """Manually trigger an ETL pipeline (admin only)."""
    get_settings()

    scheduler = getattr(request.app.state, 'etl_scheduler', None)
    if not scheduler:
        raise HTTPException(status_code=503, detail='ETL scheduler not initialized')

    valid_pipelines = ['lgd', 'boundaries', 'osm_civic', 'datagov', 'municipal', 'grievance']
    if pipeline not in valid_pipelines:
        raise HTTPException(
            status_code=400,
            detail=f'Invalid pipeline: {pipeline}. Valid: {valid_pipelines}',
        )

    result = await scheduler.run_pipeline(pipeline)
    if result:
        return {
            'pipeline': pipeline,
            'status': result.status,
            'records_fetched': result.records_fetched,
            'records_inserted': result.records_inserted,
            'records_updated': result.records_updated,
            'records_skipped': result.records_skipped,
            'error': result.error_message,
        }
    return {'pipeline': pipeline, 'status': 'failed', 'error': 'Pipeline execution failed'}


@limiter.limit("5/minute")
@router.get('/admin/civic/etl-log')
async def get_etl_log(request: Request, 
    pipeline: str | None = Query(None),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Get ETL run history."""
    stmt = select(ETLRunLog).order_by(ETLRunLog.started_at.desc())
    if pipeline:
        stmt = stmt.where(ETLRunLog.pipeline_name == pipeline)
    stmt = stmt.limit(limit)

    result = await db.execute(stmt)
    logs = result.scalars().all()

    return {
        'logs': [
            {
                'id': l.id, 'pipeline': l.pipeline_name,
                'started_at': l.started_at.isoformat(),
                'finished_at': l.finished_at.isoformat() if l.finished_at else None,
                'status': l.status,
                'records_fetched': l.records_fetched,
                'records_inserted': l.records_inserted,
                'records_updated': l.records_updated,
                'records_skipped': l.records_skipped,
                'error': l.error_message,
            }
            for l in logs
        ],
    }


@limiter.limit("5/minute")
@router.post('/admin/civic/export')
async def export_civic_data(request: Request, 
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(require_role(Role.OPERATOR)),
) -> dict[str, Any]:
    """Export all civic data to JSON files for HuggingFace Hub (admin only)."""
    logger.info('Admin export_civic_data called by %s from %s',
                current_user.get('sub', 'unknown'),
                request.client.host if request.client else 'unknown')
    """
    Exports:
    - LGD hierarchy (states/districts/subdistricts/villages)
    - Admin boundaries (GeoJSON)
    - OSM civic features
    - Government datasets
    - Municipal features
    - Grievances
    - Municipalities (GeoJSON)

    Output goes to backend/data/civic_intel/ for HuggingFace Hub upload.
    """

    from services.civic_intel.data_exporter import CivicDataExporter

    exporter = CivicDataExporter()
    manifest = await exporter.export_all(db)

    return {
        'status': 'success',
        'export_dir': str(exporter.export_dir),
        'manifest': manifest,
    }


# ──────────────────────────────────────────────────────────
# COMPLAINT CLUSTERING & HOTSPOTS
# ──────────────────────────────────────────────────────────

@limiter.limit("20/minute")
@router.get('/civic/clusters')
async def get_complaint_clusters(request: Request, 
    city: str | None = Query(None),
    ward_id: str | None = Query(None),
    eps_meters: float = Query(200, description='DBSCAN neighborhood radius in meters'),
    min_samples: int = Query(3, description='Minimum complaints per cluster'),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """DBSCAN spatial clustering of complaints to detect hotspots."""
    from services.complaint_cluster import ComplaintClusterService

    clusters = await ComplaintClusterService.find_clusters(
        db, city=city, ward_id=ward_id,
        eps_meters=eps_meters, min_samples=min_samples,
    )
    return {
        'total_clusters': len(clusters),
        'clusters': [
            {
                'cluster_id': c.cluster_id,
                'lat': c.centroid_lat,
                'lon': c.centroid_lon,
                'complaint_count': c.point_count,
                'radius_m': c.radius_meters,
                'dominant_type': c.dominant_issue_type,
                'avg_severity': c.avg_severity,
                'issue_types': c.issue_types,
            }
            for c in clusters
        ],
    }


@limiter.limit("20/minute")
@router.get('/civic/hotspots')
async def get_hotspots(request: Request, 
    city: str | None = Query(None),
    top_n: int = Query(10, le=50),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Get top N complaint hotspots for command center heatmap."""
    from services.complaint_cluster import ComplaintClusterService

    hotspots = await ComplaintClusterService.get_hotspots(db, city=city, top_n=top_n)
    return {'hotspots': hotspots}


# ──────────────────────────────────────────────────────────
# ESCALATION PREDICTION
# ──────────────────────────────────────────────────────────

@limiter.limit("20/minute")
@router.get('/civic/escalation-risk')
async def get_escalation_risk(request: Request, 
    city: str | None = Query(None),
    min_risk: float = Query(0.25, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """AI escalation prediction for open complaints."""
    from services.escalation_predictor import EscalationPredictor

    predictions = await EscalationPredictor.batch_predict(
        db, city=city, min_risk=min_risk,
    )
    return {
        'total_at_risk': len(predictions),
        'predictions': [
            {
                'issue_uuid': p.issue_uuid,
                'risk_score': p.risk_score,
                'risk_level': p.risk_level,
                'contributing_factors': p.contributing_factors,
                'recommended_action': p.recommended_action,
                'predicted_escalation_hours': p.predicted_escalation_hours,
            }
            for p in predictions
        ],
    }


# ──────────────────────────────────────────────────────────
# STREETLIGHT ASSET REGISTRY
# ──────────────────────────────────────────────────────────

@limiter.limit("20/minute")
@router.get('/civic/streetlights/qr/{qr_code}')
async def lookup_streetlight_qr(request: Request, 
    qr_code: str,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Look up a streetlight pole by QR code (citizen scan flow)."""
    from services.streetlight_service import StreetlightService

    pole = await StreetlightService.lookup_by_qr(db, qr_code)
    if not pole:
        raise HTTPException(status_code=404, detail='Pole not found')
    return {
        'pole_id': pole.pole_id,
        'qr_code': pole.qr_code,
        'city': pole.city,
        'ward_id': pole.ward_id,
        'street_name': pole.street_name,
        'is_operational': pole.is_operational,
        'lamp_type': pole.lamp_type,
        'wattage': pole.wattage,
        'failure_count': pole.failure_count,
        'last_maintenance': pole.last_maintenance.isoformat() if pole.last_maintenance else None,
        'authority': pole.authority,
    }


@limiter.limit("20/minute")
@router.get('/civic/streetlights/nearby')
async def nearby_streetlights(request: Request, 
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius: int = Query(500, le=2000),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Find streetlight poles near a location."""
    from services.streetlight_service import StreetlightService

    poles = await StreetlightService.find_nearby(db, lat, lon, radius)
    return {
        'total': len(poles),
        'poles': [
            {
                'pole_id': p.pole_id,
                'qr_code': p.qr_code,
                'is_operational': p.is_operational,
                'lamp_type': p.lamp_type,
                'failure_count': p.failure_count,
            }
            for p in poles
        ],
    }


@limiter.limit("10/minute")
@router.post('/civic/streetlights/{pole_id}/outage')
async def report_streetlight_outage(request: Request, 
    pole_id: str,
    notes: str | None = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Report a streetlight outage (citizen endpoint)."""
    from services.streetlight_service import StreetlightService

    pole = await StreetlightService.report_outage(db, pole_id, notes)
    if not pole:
        raise HTTPException(status_code=404, detail='Pole not found')
    return {
        'status': 'outage_recorded',
        'pole_id': pole.pole_id,
        'failure_count': pole.failure_count,
    }


@limiter.limit("20/minute")
@router.get('/civic/streetlights/maintenance-prediction')
async def streetlight_maintenance_prediction(request: Request, 
    city: str | None = Query(None),
    top_n: int = Query(20, le=100),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Predictive maintenance ranking for streetlight poles."""
    from services.streetlight_service import StreetlightService

    predictions = await StreetlightService.predict_maintenance(db, city=city, top_n=top_n)
    return {'predictions': predictions}


# ──────────────────────────────────────────────────────────
# OFFICER ROUTE OPTIMIZATION
# ──────────────────────────────────────────────────────────

@limiter.limit("20/minute")
@router.get('/civic/officer/route')
async def get_officer_route(request: Request, 
    officer_id: str = Query(...),
    lat: float = Query(..., description='Officer current latitude'),
    lon: float = Query(..., description='Officer current longitude'),
    city: str | None = Query(None),
    ward_id: str | None = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Generate optimized visit route for a field officer."""
    from services.officer_route_optimizer import OfficerRouteOptimizer

    route = await OfficerRouteOptimizer.optimize_route(
        db, officer_id=officer_id, officer_lat=lat, officer_lon=lon,
        city=city, ward_id=ward_id,
    )
    return {
        'officer_id': route.officer_id,
        'total_stops': route.total_stops,
        'total_distance_km': route.total_distance_km,
        'estimated_duration_minutes': route.estimated_duration_minutes,
        'warnings': route.warnings,
        'stops': [
            {
                'order': s.order,
                'complaint_ref': s.complaint_ref,
                'issue_type': s.issue_type,
                'severity': s.severity,
                'lat': s.lat,
                'lon': s.lon,
                'distance_from_prev_km': s.distance_from_prev_km,
                'estimated_arrival_minutes': s.estimated_arrival_minutes,
                'ward_id': s.ward_id,
            }
            for s in route.stops
        ],
    }

