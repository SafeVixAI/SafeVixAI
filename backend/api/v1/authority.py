# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Authority Acceptance API for SafeVixAI.

Endpoints for authorities/officers to accept, reject, reassign, escalate,
or request clarification on assigned complaints.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.limiter import limiter
from core.rbac import Role, require_role
from models.road_issue import RoadIssue
from services.complaint_state_machine import ComplaintStateMachine, InvalidTransitionError

router = APIRouter(prefix='/api/v1/authority', tags=['Authority Workflow'])


class AcceptRequest(BaseModel):
    notes: str | None = None

class RejectRequest(BaseModel):
    reason: str = Field(..., min_length=5, description="Reason for rejection (required)")

class ReassignRequest(BaseModel):
    target_officer_id: str = Field(..., description="Officer UUID to reassign to")
    reason: str | None = None

class EscalateRequest(BaseModel):
    reason: str = Field(..., min_length=5)
    target_tier: int | None = Field(default=None, ge=1, le=5)

class ClarificationRequest(BaseModel):
    question: str = Field(..., min_length=5, description="Question to ask citizen")


@router.post('/complaints/{issue_uuid}/accept')
@limiter.limit("30/minute")
async def accept_complaint(
    request: Request,
    issue_uuid: str,
    body: AcceptRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(Role.FIELD_OFFICER)),
) -> dict:
    """Officer accepts a complaint assignment. Starts SLA tracking."""
    try:
        cid = uuid.UUID(issue_uuid)
        actor_id = uuid.UUID(current_user["sub"]) if "sub" in current_user else None
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        result = await ComplaintStateMachine.transition(
            db,
            complaint_uuid=cid,
            target_status="accepted",
            actor_id=actor_id,
            actor_role="field_officer",
            notes=body.notes or "Officer accepted complaint assignment",
            metadata={"accepted_by_name": current_user.get("name", "Unknown")},
        )
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "status": "accepted",
        "complaint_ref": result.issue.complaint_ref if result.issue else None,
        "new_status": result.new_status,
        "accepted_at": datetime.now(UTC).isoformat(),
    }


@router.post('/complaints/{issue_uuid}/reject')
@limiter.limit("15/minute")
async def reject_complaint(
    request: Request,
    issue_uuid: str,
    body: RejectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(Role.FIELD_OFFICER)),
) -> dict:
    """Officer rejects complaint (must provide reason). Triggers reassignment."""
    try:
        cid = uuid.UUID(issue_uuid)
        actor_id = uuid.UUID(current_user["sub"]) if "sub" in current_user else None
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        result = await ComplaintStateMachine.transition(
            db,
            complaint_uuid=cid,
            target_status="reassigned",
            actor_id=actor_id,
            actor_role="field_officer",
            notes=f"Rejected by officer: {body.reason}",
            metadata={
                "rejection_reason": body.reason,
                "rejected_by": current_user.get("name", "Unknown"),
            },
        )
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Store rejection reason on issue
    if result.issue:
        result.issue.rejection_reason = body.reason
        result.issue.assigned_officer_id = None  # Clear assignment
        await db.commit()

    # Attempt auto-reassignment via workload balancer
    reassigned_to = None
    if result.issue:
        try:
            from services.workload_balancer import WorkloadBalancer
            lat = float((await db.execute(
                select(func.ST_Y(result.issue.location))
            )).scalar() or 0)
            lon = float((await db.execute(
                select(func.ST_X(result.issue.location))
            )).scalar() or 0)

            best = await WorkloadBalancer.find_best_officer(
                db,
                complaint_lat=lat,
                complaint_lon=lon,
                ward_id=result.issue.ward_id,
                severity=result.issue.severity,
            )
            if best:
                result.issue.assigned_officer_id = uuid.UUID(best.officer_id)
                await ComplaintStateMachine.transition(
                    db,
                    complaint_uuid=cid,
                    target_status="assigned",
                    notes=f"Auto-reassigned to {best.officer_name} after rejection",
                    metadata={"workload_score": best.composite_score},
                )
                reassigned_to = best.officer_name
        except Exception as e:
            logger.warning("Auto-reassignment failed: %s", e)

    return {
        "status": "rejected_and_reassigning",
        "reason": body.reason,
        "reassigned_to": reassigned_to,
    }


@router.post('/complaints/{issue_uuid}/escalate')
@limiter.limit("10/minute")
async def escalate_complaint(
    request: Request,
    issue_uuid: str,
    body: EscalateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(Role.FIELD_OFFICER)),
) -> dict:
    """Manually escalate a complaint to higher authority."""
    try:
        cid = uuid.UUID(issue_uuid)
        actor_id = uuid.UUID(current_user["sub"]) if "sub" in current_user else None
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        result = await ComplaintStateMachine.escalate(
            db,
            complaint_uuid=cid,
            reason=body.reason,
            escalation_tier=body.target_tier,
            actor_id=actor_id,
            actor_role="field_officer",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "status": "escalated",
        "new_severity": result.issue.severity if result.issue else None,
        "reason": body.reason,
    }


@router.get('/pending')
@limiter.limit("20/minute")
async def get_pending_complaints(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(Role.FIELD_OFFICER)),
) -> list[dict]:
    """Get unaccepted complaints assigned to the logged-in officer."""
    try:
        officer_id = uuid.UUID(current_user["sub"])
    except (ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid user token")

    stmt = (
        select(RoadIssue)
        .where(RoadIssue.assigned_officer_id == officer_id)
        .where(RoadIssue.status.in_(["assigned"]))
        .order_by(RoadIssue.severity.desc(), RoadIssue.created_at.asc())
    )
    issues = (await db.execute(stmt)).scalars().all()

    return [
        {
            "uuid": str(i.uuid),
            "complaint_ref": i.complaint_ref,
            "issue_type": i.issue_type,
            "severity": i.severity,
            "category": i.category,
            "ward_name": i.ward_name,
            "location_address": i.location_address,
            "status": i.status,
            "sla_deadline": i.sla_deadline.isoformat() if i.sla_deadline else None,
            "created_at": i.created_at.isoformat() if i.created_at else None,
            "allowed_actions": ComplaintStateMachine.get_allowed_transitions(i.status),
        }
        for i in issues
    ]


import logging  # noqa: E402

logger = logging.getLogger(__name__)
