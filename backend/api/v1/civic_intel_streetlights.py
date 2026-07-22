# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Streetlight asset registry routes — QR lookup, nearby, outage reporting, maintenance prediction."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=['Civic Intelligence'])


@limiter.limit("20/minute")
@router.get('/civic/streetlights/qr/{qr_code}')
async def lookup_streetlight_qr(
    request: Request,
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
async def nearby_streetlights(
    request: Request,
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
async def report_streetlight_outage(
    request: Request,
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
async def streetlight_maintenance_prediction(
    request: Request,
    city: str | None = Query(None),
    top_n: int = Query(20, le=100),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Predictive maintenance ranking for streetlight poles."""
    from services.streetlight_service import StreetlightService

    predictions = await StreetlightService.predict_maintenance(db, city=city, top_n=top_n)
    return {'predictions': predictions}
