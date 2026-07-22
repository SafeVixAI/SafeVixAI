# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from fastapi import APIRouter, Depends, Request

from core.limiter import limiter
from core.security import get_current_user
from models.schemas import GarageSyncResponse
from services.garage_service import GarageService

router = APIRouter(prefix="/api/v1/garage", tags=["Garage"])

@router.post("/sync", response_model=GarageSyncResponse)
@limiter.limit("10/minute")
async def sync_user_garage(
    request: Request,
    vehicle_number: str | None = None,
    current_user: dict = Depends(get_current_user),
) -> GarageSyncResponse:
    """
    Synchronize user vehicles with Transport Department RTO / Parivahan registers.
    """
    user_id = str(current_user["sub"])
    cache = getattr(request.app.state, "cache", None)
    return await GarageService.sync_vehicles(user_id, vehicle_number, cache=cache)

