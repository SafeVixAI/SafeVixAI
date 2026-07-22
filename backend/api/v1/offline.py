# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.limiter import limiter
from services.emergency_locator import EmergencyLocatorService
from services.exceptions import ServiceValidationError

router = APIRouter(prefix='/api/v1/offline', tags=['Offline'])


def get_emergency_service(request: Request) -> EmergencyLocatorService:
    return request.app.state.emergency_service


@router.get('/bundle/{city}')
@limiter.limit("10/minute")
async def get_offline_bundle(
    request: Request,
    city: str = Path(min_length=2, max_length=64, pattern=r'^[A-Za-z][A-Za-z\s-]*$'),
    db: AsyncSession = Depends(get_db),
    emergency_service: EmergencyLocatorService = Depends(get_emergency_service),
) -> dict:
    try:
        return await emergency_service.build_city_bundle(db=db, city=city)
    except ServiceValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
