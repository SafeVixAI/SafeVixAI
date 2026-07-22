# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from core.limiter import limiter
from models.schemas import RoutePreviewResponse, RouteProfile
from services.exceptions import ExternalServiceError, ServiceValidationError
from services.routing_service import RoutingService
from services.safe_routing import get_safe_route

router = APIRouter(prefix='/api/v1/routing', tags=['Routing'])


def get_routing_service(request: Request) -> RoutingService:
    return request.app.state.routing_service


@router.get('/preview', response_model=RoutePreviewResponse)
@limiter.limit("30/minute")
async def preview_route(
    request: Request,
    origin_lat: float = Query(..., ge=-90, le=90),
    origin_lon: float = Query(..., ge=-180, le=180),
    destination_lat: float = Query(..., ge=-90, le=90),
    destination_lon: float = Query(..., ge=-180, le=180),
    profile: RouteProfile = Query(default='driving-car'),
    alternatives: int = Query(default=2, ge=0, le=2),
    routing_service: RoutingService = Depends(get_routing_service),
) -> RoutePreviewResponse:
    try:
        return await routing_service.preview_route(
            origin_lat=origin_lat,
            origin_lon=origin_lon,
            destination_lat=destination_lat,
            destination_lon=destination_lon,
            profile=profile,
            alternatives=alternatives,
        )
    except ServiceValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ExternalServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get('/safe-route')
@limiter.limit("20/minute")
async def get_safe_route_endpoint(
    request: Request,
    origin_lat: float = Query(..., ge=-90, le=90),
    origin_lon: float = Query(..., ge=-180, le=180),
    destination_lat: float = Query(..., ge=-90, le=90),
    destination_lon: float = Query(..., ge=-180, le=180),
    prefer_safety: bool = Query(default=False),
) -> dict:
    """
    Returns a safe route prioritizing well-lit, non-isolated roads using ORS.
    """
    try:
        return await get_safe_route(
            origin=(origin_lat, origin_lon),
            dest=(destination_lat, destination_lon),
            prefer_safety=prefer_safety,
        )
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning('Safe routing error: %s', exc)
        raise HTTPException(status_code=503, detail='Safe routing service temporarily unavailable.') from exc
