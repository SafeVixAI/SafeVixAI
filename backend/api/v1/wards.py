# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.limiter import limiter
from models.schemas import WardResponse, WardStatsResponse
from services.ward_service import WardService

router = APIRouter(prefix='/api/v1/wards', tags=['Wards'])


@router.get('', response_model=list[WardResponse])
@limiter.limit("30/minute")
async def list_all_wards(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> list[WardResponse]:
    """List all Chennai wards."""
    wards = await WardService.list_all_wards(db)
    return [
        WardResponse(
            ward_id=w.ward_id,
            ward_name=w.ward_name,
            zone_name=w.zone_name,
            city=w.city,
            state_code=w.state_code,
            population=w.population,
            area_sqkm=w.area_sqkm
        )
        for w in wards
    ]


@router.get('/locate', response_model=WardResponse)
@limiter.limit("30/minute")
async def locate_ward_by_coordinates(
    request: Request,
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    db: AsyncSession = Depends(get_db)
) -> WardResponse:
    """Find the ward containing the given lat/lon point."""
    ward = await WardService.find_ward_by_coordinates(db, lat=lat, lon=lon)
    if not ward:
        raise HTTPException(status_code=404, detail="No ward found at these coordinates.")

    return WardResponse(
        ward_id=ward.ward_id,
        ward_name=ward.ward_name,
        zone_name=ward.zone_name,
        city=ward.city,
        state_code=ward.state_code,
        population=ward.population,
        area_sqkm=ward.area_sqkm
    )


@router.get('/{ward_id}/stats', response_model=WardStatsResponse)
@limiter.limit("30/minute")
async def get_ward_stats(
    request: Request,
    ward_id: str,
    db: AsyncSession = Depends(get_db)
) -> WardStatsResponse:
    """Get metrics and resolution rates for a ward."""
    # Verify ward exists
    from sqlalchemy import select

    from models.ward import Ward
    stmt = select(Ward).where(Ward.ward_id == ward_id)
    ward = (await db.execute(stmt)).scalar_one_or_none()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found.")

    stats = await WardService.get_ward_stats(db, ward_id)
    return WardStatsResponse(**stats)
