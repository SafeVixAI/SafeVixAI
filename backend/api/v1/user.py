# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.audit import AuditEvent, AuditLog
from core.database import get_db
from core.limiter import limiter
from core.security import get_current_user
from models.road_issue import RoadIssue
from models.schemas import (
    UserDataExport,
    UserDeleteResponse,
    UserProfileCreate,
    UserProfileResponse,
    UserProfileUpdate,
)
from models.sos_incident import SosIncident
from models.user import UserProfile

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.post("/", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_user_profile(
    request: Request,
    profile_data: UserProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Any:
    """Create a new emergency user profile."""
    contacts = [contact.model_dump() for contact in profile_data.emergency_contacts]

    db_profile = UserProfile(
        user_id=str(current_user["sub"]),
        name=profile_data.name,
        blood_group=profile_data.blood_group,
        emergency_contacts=contacts,
        allergies=profile_data.allergies,
        vehicle_details=profile_data.vehicle_details,
        medical_notes=profile_data.medical_notes,
    )
    db.add(db_profile)
    await db.commit()
    await db.refresh(db_profile)
    return db_profile


@router.get("/{user_id}", response_model=UserProfileResponse)
@limiter.limit("30/minute")
async def get_user_profile(
    request: Request,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Any:
    """Fetch the caller's emergency profile by ID."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.id == user_id, UserProfile.user_id == str(current_user["sub"]))
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency profile not found"
        )
    return profile


@router.put("/{user_id}", response_model=UserProfileResponse)
@limiter.limit("10/minute")
async def update_user_profile(
    request: Request,
    user_id: uuid.UUID,
    profile_update: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Any:
    """Update an existing emergency user profile."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.id == user_id, UserProfile.user_id == str(current_user["sub"]))
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency profile not found"
        )

    update_data = profile_update.model_dump(exclude_unset=True)

    if "emergency_contacts" in update_data and update_data["emergency_contacts"] is not None:
        update_data["emergency_contacts"] = [contact for contact in update_data["emergency_contacts"]]

    for key, value in update_data.items():
        setattr(profile, key, value)

    await db.commit()
    await db.refresh(profile)
    ip = request.client.host if request.client else "unknown"
    AuditLog.log(AuditEvent.PROFILE_UPDATE, user_id=str(current_user["sub"]), ip_address=ip, details={"updated_fields": list(update_data.keys())})
    return profile


@router.get("/{user_id}/export", response_model=UserDataExport)
@limiter.limit("5/minute")
async def export_user_data(
    request: Request,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Any:
    """GDPR: Export all user data (profile + SOS incidents + road reports)."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.id == user_id, UserProfile.user_id == str(current_user["sub"]))
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    sos_result = await db.execute(
        select(SosIncident).where(SosIncident.user_id == str(current_user["sub"]))
    )
    sos_incidents = [sos_row.to_dict() if hasattr(sos_row, 'to_dict') else {
        "id": str(sos_row.id),
        "lat": sos_row.lat,
        "lon": sos_row.lon,
        "created_at": str(sos_row.created_at),
    } for sos_row in sos_result.scalars().all()]

    road_result = await db.execute(
        select(RoadIssue).where(RoadIssue.reporter_id == str(current_user["sub"]))
    )
    road_reports = [{
        "uuid": str(r.uuid),
        "issue_type": r.issue_type,
        "severity": r.severity,
        "description": r.description,
        "status": r.status,
        "created_at": str(r.created_at),
    } for r in road_result.scalars().all()]

    return UserDataExport(
        profile=profile,
        sos_incidents=sos_incidents,
        road_reports=road_reports,
    )


@router.delete("/{user_id}", response_model=UserDeleteResponse)
@limiter.limit("3/minute")
async def delete_user_data(
    request: Request,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Any:
    """GDPR: Delete user profile and all related data."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.id == user_id, UserProfile.user_id == str(current_user["sub"]))
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    sos_result = await db.execute(
        sa_delete(SosIncident).where(SosIncident.user_id == str(current_user["sub"])).returning(SosIncident.id)
    )
    deleted_sos = len(sos_result.all())

    road_result = await db.execute(
        sa_delete(RoadIssue).where(RoadIssue.reporter_id == str(current_user["sub"])).returning(RoadIssue.uuid)
    )
    deleted_roads = len(road_result.all())

    await db.delete(profile)
    await db.commit()
    ip = request.client.host if request.client else "unknown"
    AuditLog.log(AuditEvent.PROFILE_UPDATE, user_id=str(current_user["sub"]), ip_address=ip, details={"action": "user_deletion", "deleted_sos": deleted_sos, "deleted_roads": deleted_roads})

    return UserDeleteResponse(
        status="ok",
        message="All user data deleted",
        deleted_profile=True,
        deleted_sos_incidents=deleted_sos,
        deleted_road_reports=deleted_roads,
    )
