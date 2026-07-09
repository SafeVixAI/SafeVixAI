# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Municipality civic hub routes — MeraWard-style directory, profiles, wards."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.limiter import limiter
from core.database import get_async_session
from models.municipality import Municipality
from models.municipal_feature import MunicipalFeature

logger = logging.getLogger(__name__)

router = APIRouter(tags=['Civic Intelligence'])


@limiter.limit("20/minute")
@router.get('/civic/municipalities')
async def list_municipalities(
    request: Request,
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
async def nearby_municipality(
    request: Request,
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
async def get_municipality(
    request: Request,
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
async def get_municipality_stats(
    request: Request,
    slug: str,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Get local complaint/grievance stats for a municipality."""
    from services.civic_intel.civic_analytics_service import CivicAnalyticsService
    return await CivicAnalyticsService.get_municipality_stats(db, slug)


@limiter.limit("20/minute")
@router.get('/civic/municipalities/{slug}/wards')
async def get_municipality_wards(
    request: Request,
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
