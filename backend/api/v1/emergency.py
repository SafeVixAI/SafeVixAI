# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import sys
import time
from pathlib import Path

for parent in Path(__file__).resolve().parents:
    if (parent / 'alert_service.py').exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.alert import get_alert_service
from core.audit import AuditLog
from core.database import get_db
from core.limiter import limiter
from core.metrics import (
    emergency_lookup_time,
    emergency_lookup_total,
    emergency_services_found,
    sos_dispatch_total,
    sos_response_time,
)
from core.security import get_current_user_optional
from models.schemas import EmergencyNumbersResponse, EmergencyResponse, SosResponse
from models.sos_incident import SosIncident
from services.emergency_locator import EMERGENCY_NUMBERS, EmergencyLocatorService
from services.exceptions import ExternalServiceError

router = APIRouter(prefix='/api/v1/emergency', tags=['Emergency'])


def get_emergency_service(request: Request) -> EmergencyLocatorService:
    return request.app.state.emergency_service


@router.get('/nearby', response_model=EmergencyResponse)
@limiter.limit("30/minute")
async def get_nearby_services(
    request: Request,
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    categories: str | None = Query(default=None, description='Comma-separated emergency categories'),
    radius: int | None = Query(default=None, ge=100, le=50000),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    emergency_service: EmergencyLocatorService = Depends(get_emergency_service),
) -> EmergencyResponse:
    """
    Retrieve nearest active emergency responder stations and services.

    Queries database and Overpass API to locate nearby medical, police, fire, 
    and highway helpline responders filtered by dynamic radius and categories.

    Args:
        request: The FastAPI request instance.
        lat: Latitude of search centroid (degrees, -90 to 90).
        lon: Longitude of search centroid (degrees, -180 to 180).
        categories: Optional comma-separated list of emergency categories.
        radius: Search radius in meters (100m to 50km). Defaults to service config.
        limit: Max number of records to return (1 to 50).
        offset: Pagination offset index.
        db: Database session injection.
        emergency_service: Emergency locator service layer.

    Returns:
        EmergencyResponse containing lists of matched emergency facilities and metadata.

    Raises:
        HTTPException (503): When upstream geospatial Overpass query fails.
    """
    try:
        return await emergency_service.find_nearby(
            db=db,
            lat=lat,
            lon=lon,
            categories=categories,
            radius=radius,
            limit=limit,
            offset=offset,
        )
    except ExternalServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get('/sos', response_model=SosResponse)
@limiter.limit("20/minute")
async def get_sos_payload(
    request: Request,
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    db: AsyncSession = Depends(get_db),
    emergency_service: EmergencyLocatorService = Depends(get_emergency_service),
) -> SosResponse:
    """
    Synthesize an emergency SOS response package for offline/online sync.

    Fetches critical numbers, nearby hospitals, and police contacts based on 
    current GPS coordinates, optimized to keep offline sync payloads lightweight.

    Args:
        request: The FastAPI request instance.
        lat: Latitude of distress point.
        lon: Longitude of distress point.
        db: Database session injection.
        emergency_service: Emergency locator service layer.

    Returns:
        SosResponse including localized service contacts and fallback coordinates.

    Raises:
        HTTPException (503): When contact synthesis or geo-resolution fails.
    """
    try:
        return await emergency_service.build_sos_payload(db=db, lat=lat, lon=lon)
    except ExternalServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post('/sos', response_model=SosResponse)
@limiter.limit("10/minute")
async def create_sos_incident(
    request: Request,
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    db: AsyncSession = Depends(get_db),
    emergency_service: EmergencyLocatorService = Depends(get_emergency_service),
    current_user: dict | None = Depends(get_current_user_optional),
) -> SosResponse:
    """
    Register a live panic SOS incident and dispatch rescue operations.

    Logs a panic trigger, records user-agent metadata, records response metrics,
    and returns localized emergency numbers and facilities for coordinate rescue.

    Args:
        request: The FastAPI request instance.
        lat: Latitude of user at distress initiation.
        lon: Longitude of user at distress initiation.
        db: Database session injection.
        emergency_service: Emergency locator service layer.
        current_user: Optional authenticated user context from bearer token.

    Returns:
        SosResponse detailing dispatched incident context and surrounding resources.

    Raises:
        HTTPException (503): If incident recording or DB serialization commits fail.
    """
    start = time.monotonic()
    try:
        incident = SosIncident(
            user_id=str(current_user["sub"]) if current_user else None,
            lat=lat,
            lon=lon,
            user_agent=request.headers.get('user-agent', '')[:255],
        )
        db.add(incident)
        await db.commit()
        user_id = str(current_user["sub"]) if current_user else None
        ip = request.client.host if request.client else "unknown"
        AuditLog.log_sos_trigger(user_id, lat, lon, ip)

        result = await emergency_service.build_sos_payload(db=db, lat=lat, lon=lon)

        # Record SOS metrics
        duration = time.monotonic() - start
        sos_response_time.observe(duration)
        sos_dispatch_total.labels(status="success", mode="online").inc()

        # Record emergency lookup metrics
        emergency_lookup_total.labels(
            service_type="all",
            source="overpass",
        ).inc()
        emergency_lookup_time.labels(service_type="all").observe(duration)

        # Record services found
        if hasattr(result, 'count'):
            emergency_services_found.labels(
                service_type="all",
                radius_meters=5000,
            ).set(result.count)

        return result
    except ExternalServiceError as exc:
        sos_dispatch_total.labels(status="failed", mode="online").inc()
        get_alert_service().alert_external_api_failed(
            service_name="SOS Dispatch",
            endpoint=f"POST /api/v1/emergency/sos lat={lat} lon={lon}",
            status_code=503,
            error_msg=f"External service error: {exc}",
        )
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        await db.rollback()
        sos_dispatch_total.labels(status="failed", mode="online").inc()
        get_alert_service().alert_external_api_failed(
            service_name="SOS Dispatch",
            endpoint=f"POST /api/v1/emergency/sos lat={lat} lon={lon}",
            status_code=500,
            error_msg=f"Unexpected SOS error: {exc}",
        )
        raise HTTPException(status_code=503, detail="Unable to record SOS incident") from exc


@router.get('/numbers', response_model=EmergencyNumbersResponse)
@limiter.limit("30/minute")
async def get_emergency_numbers(
    request: Request,
) -> EmergencyNumbersResponse:
    """
    Retrieve national static emergency responder hotlines.

    Returns the unified catalog of primary emergency dispatch numbers including 
    Police, Ambulance, Fire, Women Helpline, and National Emergency Response.

    Args:
        request: The FastAPI request instance.

    Returns:
        EmergencyNumbersResponse containing verified hotline strings.
    """
    return EMERGENCY_NUMBERS


@router.get('/safe-spaces')
@limiter.limit("20/minute")
async def safe_spaces(
    request: Request,
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius: int = Query(default=1000, ge=100, le=50000),
) -> dict:
    """
    Identify secure spaces and localized emergency resources for women safety.

    Queries police checkpoints, transit terminals, and operational municipal 
    buildings within a specified circular search radius.

    Args:
        request: The FastAPI request instance.
        lat: Latitude coordinate of current position.
        lon: Longitude coordinate of current position.
        radius: Geospatial search boundary radius in meters (100m to 50km).

    Returns:
        A dictionary containing safe zones and resource coordinates.
    """
    from services.safe_spaces import get_safe_spaces
    return await get_safe_spaces(lat, lon, radius)
