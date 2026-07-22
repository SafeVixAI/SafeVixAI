# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Citizen Verification API for SafeVixAI.

Public-facing endpoints for citizens to:
- Track complaints by reference number (no login required)
- Confirm or reject officer resolution
- Rate satisfaction
- View full audit timeline
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.limiter import limiter
from models.complaint_event import ComplaintEvent
from models.road_issue import RoadIssue
from services.complaint_state_machine import ComplaintStateMachine, InvalidTransitionError

logger = logging.getLogger("safevixai.citizen")

router = APIRouter(prefix='/api/v1/citizen', tags=['Citizen Verification'])


class ConfirmRequest(BaseModel):
    citizen_phone: str | None = Field(default=None, description="Phone for verification")
    comments: str | None = None

class RejectRequest(BaseModel):
    reason: str = Field(..., min_length=5, description="Why resolution is unsatisfactory")
    citizen_phone: str | None = None

class RatingRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Satisfaction rating 1-5")
    feedback: str | None = None


@router.get('/complaints/{complaint_ref}')
@limiter.limit("30/minute")
async def track_complaint(
    request: Request,
    complaint_ref: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Public complaint tracking by reference number. No login required.
    Returns anonymized complaint info and current status.
    """
    issue = (await db.execute(
        select(RoadIssue).where(RoadIssue.complaint_ref == complaint_ref)
    )).scalar_one_or_none()

    if not issue:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Get coordinates
    lat, lon = None, None
    if issue.location:
        try:
            row = (await db.execute(
                select(func.ST_Y(RoadIssue.location), func.ST_X(RoadIssue.location))
                .where(RoadIssue.uuid == issue.uuid)
            )).first()
            if row:
                lat, lon = float(row[0]), float(row[1])
        except Exception:
            logger.debug("Citizen resolve — location coordinates unavailable for issue %s", issue.uuid)

    # Calculate SLA status
    sla_status = "on_track"
    sla_hours_remaining = None
    if issue.sla_deadline:
        now = datetime.now(UTC).replace(tzinfo=None)
        diff = (issue.sla_deadline - now).total_seconds() / 3600
        if diff < 0:
            sla_status = "breached"
            sla_hours_remaining = round(diff, 1)
        elif diff < 4:
            sla_status = "critical"
            sla_hours_remaining = round(diff, 1)
        elif diff < 12:
            sla_status = "approaching"
            sla_hours_remaining = round(diff, 1)
        else:
            sla_hours_remaining = round(diff, 1)

    # Allowed citizen actions
    allowed_actions = []
    if issue.status == "resolved":
        allowed_actions = ["confirm", "reject"]
    elif issue.status in ("citizen_confirmed", "closed"):
        allowed_actions = ["rate"]

    return {
        "complaint_ref": issue.complaint_ref,
        "status": issue.status,
        "category": issue.category,
        "issue_type": issue.issue_type,
        "severity": issue.severity,
        "description": issue.description,
        "location_address": issue.location_address,
        "ward_name": issue.ward_name,
        "road_name": issue.road_name,
        "authority_name": issue.authority_name,
        "lat": lat,
        "lon": lon,
        "before_photo_url": issue.before_photo_url,
        "after_photo_url": issue.after_photo_url,
        "created_at": issue.created_at.isoformat() if issue.created_at else None,
        "resolved_at": issue.resolved_at.isoformat() if issue.resolved_at else None,
        "sla_status": sla_status,
        "sla_hours_remaining": sla_hours_remaining,
        "confirmation_count": issue.confirmation_count,
        "reopen_count": getattr(issue, 'reopen_count', 0) or 0,
        "allowed_actions": allowed_actions,
    }


@router.post('/complaints/{complaint_ref}/confirm')
@limiter.limit("10/minute")
async def confirm_resolution(
    request: Request,
    complaint_ref: str,
    body: ConfirmRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Citizen confirms that the complaint was resolved satisfactorily."""
    issue = (await db.execute(
        select(RoadIssue).where(RoadIssue.complaint_ref == complaint_ref)
    )).scalar_one_or_none()

    if not issue:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if issue.status != "resolved":
        raise HTTPException(
            status_code=409,
            detail=f"Complaint is not in 'resolved' status (current: {issue.status}). Cannot confirm.",
        )

    try:
        await ComplaintStateMachine.transition(
            db,
            complaint_uuid=issue.uuid,
            target_status="citizen_confirmed",
            actor_role="citizen",
            notes=body.comments or "Citizen confirmed resolution",
            metadata={"citizen_phone": body.citizen_phone},
        )
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Auto-close after citizen confirmation
    try:
        await ComplaintStateMachine.transition(
            db,
            complaint_uuid=issue.uuid,
            target_status="closed",
            actor_role="system",
            notes="Auto-closed after citizen confirmation",
        )
    except (InvalidTransitionError, Exception) as exc:
        logger.warning("Auto-close of complaint %s failed: %s", complaint_ref, exc)

    return {
        "status": "citizen_confirmed",
        "complaint_ref": complaint_ref,
        "message": "Thank you! Your confirmation has been recorded. The complaint is now closed.",
    }


@router.post('/complaints/{complaint_ref}/reject')
@limiter.limit("10/minute")
async def reject_resolution(
    request: Request,
    complaint_ref: str,
    body: RejectRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Citizen rejects the resolution. This triggers:
    1. Status → citizen_rejected → reopened
    2. Severity increases by 1
    3. New SLA deadline calculated
    4. Escalated to supervisor tier
    """
    issue = (await db.execute(
        select(RoadIssue).where(RoadIssue.complaint_ref == complaint_ref)
    )).scalar_one_or_none()

    if not issue:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if issue.status != "resolved":
        raise HTTPException(
            status_code=409,
            detail=f"Complaint is not in 'resolved' status (current: {issue.status}). Cannot reject.",
        )

    # Transition: resolved → citizen_rejected
    try:
        await ComplaintStateMachine.transition(
            db,
            complaint_uuid=issue.uuid,
            target_status="citizen_rejected",
            actor_role="citizen",
            notes=f"Citizen rejected resolution: {body.reason}",
            metadata={"rejection_reason": body.reason, "citizen_phone": body.citizen_phone},
        )
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Auto-reopen: citizen_rejected → reopened (auto-escalates severity)
    try:
        await ComplaintStateMachine.transition(
            db,
            complaint_uuid=issue.uuid,
            target_status="reopened",
            actor_role="system",
            notes="Auto-reopened after citizen rejection. Severity escalated.",
            metadata={"previous_resolution": "citizen_rejected"},
        )
    except (InvalidTransitionError, Exception) as e:
        logger.error("Auto-reopen failed: %s", e)

    return {
        "status": "reopened",
        "complaint_ref": complaint_ref,
        "new_severity": issue.severity,
        "reopen_count": getattr(issue, 'reopen_count', 0) or 0,
        "message": "Your feedback has been recorded. The complaint has been reopened with higher priority.",
    }


@router.post('/complaints/{complaint_ref}/rate')
@limiter.limit("10/minute")
async def rate_resolution(
    request: Request,
    complaint_ref: str,
    body: RatingRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Citizen rates the resolution quality (1-5 stars)."""
    issue = (await db.execute(
        select(RoadIssue).where(RoadIssue.complaint_ref == complaint_ref)
    )).scalar_one_or_none()

    if not issue:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if issue.status not in ("citizen_confirmed", "closed", "resolved"):
        raise HTTPException(
            status_code=409,
            detail="Rating only available after resolution",
        )

    if hasattr(issue, 'citizen_rating'):
        issue.citizen_rating = body.rating

    await db.commit()

    # Log rating event
    event = ComplaintEvent(
        complaint_uuid=issue.uuid,
        event_type="rated",
        actor_role="citizen",
        notes=body.feedback or f"Citizen rated {body.rating}/5",
        event_metadata={"rating": body.rating, "feedback": body.feedback},
    )
    db.add(event)
    await db.commit()

    return {
        "status": "rated",
        "rating": body.rating,
        "message": f"Thank you for your {body.rating}-star rating!",
    }


@router.get('/complaints/{complaint_ref}/timeline')
@limiter.limit("20/minute")
async def get_complaint_timeline(
    request: Request,
    complaint_ref: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the full audit trail for a complaint (anonymized for public view)."""
    issue = (await db.execute(
        select(RoadIssue).where(RoadIssue.complaint_ref == complaint_ref)
    )).scalar_one_or_none()

    if not issue:
        raise HTTPException(status_code=404, detail="Complaint not found")

    events = (await db.execute(
        select(ComplaintEvent)
        .where(ComplaintEvent.complaint_uuid == issue.uuid)
        .order_by(ComplaintEvent.created_at.asc())
    )).scalars().all()

    return {
        "complaint_ref": complaint_ref,
        "current_status": issue.status,
        "timeline": [
            {
                "event_type": e.event_type,
                "actor_role": e.actor_role or "system",
                "notes": e.notes,
                "timestamp": e.created_at.isoformat() if e.created_at else None,
                # Anonymize: don't expose actor_id or internal metadata
            }
            for e in events
        ],
    }
