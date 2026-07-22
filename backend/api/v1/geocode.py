# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from core.limiter import limiter
from models.schemas import GeocodeResult, GeocodeSearchResponse
from services.geocoding_service import GeocodingError, GeocodingService

router = APIRouter(prefix='/api/v1/geocode', tags=['Geocode'])


def get_geocoding_service(request: Request) -> GeocodingService:
    return request.app.state.geocoding_service


@router.get('/reverse')
@limiter.limit("30/minute")
async def reverse_geocode(
    request: Request,
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    geocoding_service: GeocodingService = Depends(get_geocoding_service),
) -> GeocodeResult:
    try:
        return await geocoding_service.reverse(lat=lat, lon=lon)
    except GeocodingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get('/search', response_model=GeocodeSearchResponse)
@limiter.limit("30/minute")
async def search_geocode(
    request: Request,
    q: str = Query(..., min_length=2),
    geocoding_service: GeocodingService = Depends(get_geocoding_service),
) -> GeocodeSearchResponse:
    try:
        results = await geocoding_service.search(q)
    except GeocodingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return GeocodeSearchResponse(results=results)
