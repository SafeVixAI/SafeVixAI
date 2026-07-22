# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.limiter import limiter
from models.schemas import (
    ChallanQuery,
    ChallanResponse,
    DisputeDraftRequest,
    DisputeDraftResponse,
    FinePredictionRequest,
    FinePredictionResponse,
)
from services.challan_dispute_service import ChallanDisputeService
from services.challan_service import ChallanService
from services.exceptions import ExternalServiceError, ServiceValidationError
from services.fine_prediction_service import FinePredictionService

router = APIRouter(prefix='/api/v1/challan', tags=['Challan'])


def get_challan_service(request: Request) -> ChallanService:
    return request.app.state.challan_service


@router.post('/calculate', response_model=ChallanResponse)
@limiter.limit("20/minute")
async def calculate_challan(
    request: Request,
    payload: ChallanQuery,
    db: AsyncSession = Depends(get_db),
    challan_service: ChallanService = Depends(get_challan_service),
) -> ChallanResponse:
    """
    Calculate high-fidelity traffic challan fines and legal compliance requirements.
    """
    try:
        return await challan_service.calculate_with_db(payload, db=db)
    except ExternalServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ServiceValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post('/dispute', response_model=DisputeDraftResponse)
@limiter.limit("10/minute")
async def calculate_dispute_appeal(
    request: Request,
    payload: DisputeDraftRequest,
) -> DisputeDraftResponse:
    """
    Formulate a structured e-challan legal dispute citation and petition.
    """
    return ChallanDisputeService.draft_dispute(payload)


@router.post('/predict', response_model=FinePredictionResponse)
@limiter.limit("10/minute")
async def predict_telemetry_liability(
    request: Request,
    payload: FinePredictionRequest,
) -> FinePredictionResponse:
    """
    Analyze driver telemetry logs and calculate future fine risk scores.
    """
    return FinePredictionService.predict_liability(payload)
