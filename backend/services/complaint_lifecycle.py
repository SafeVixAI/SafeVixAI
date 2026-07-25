# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Issue lifecycle management.

Domain language: "issue" (RoadIssue) = road condition report, "complaint" (ComplaintEvent) = lifecycle event.
This service manages RoadIssue lifecycle using ComplaintEvent auditing.
"""
from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.complaint_event import ComplaintEvent
from models.officer import Officer
from models.road_issue import RoadIssue
from services.complaint_state_machine import ComplaintStateMachine

logger = logging.getLogger(__name__)


class ComplaintLifecycle:
    @staticmethod
    def calculate_sla_deadline(severity: int) -> datetime:
        """
        Calculate SLA deadline based on severity:
        - Severity 5 (Extreme): 4 hours
        - Severity 4 (Critical): 24 hours
        - Severity 3 (Serious): 72 hours
        - Severity 1-2: 7 days (168 hours)
        """
        now = datetime.now(UTC).replace(tzinfo=None)
        if severity >= 5:
            return now + timedelta(hours=4)
        elif severity == 4:
            return now + timedelta(hours=24)
        elif severity == 3:
            return now + timedelta(hours=72)
        else:
            return now + timedelta(days=7)

    @classmethod
    async def log_event(
        cls,
        db: AsyncSession,
        *,
        complaint_uuid: uuid.UUID,
        event_type: str,
        actor_id: uuid.UUID | None = None,
        actor_role: str | None = None,
        notes: str | None = None,
        metadata: dict | None = None
    ) -> ComplaintEvent:
        """Helper to create and commit an audit trail event for a complaint."""
        event = ComplaintEvent(
            complaint_uuid=complaint_uuid,
            event_type=event_type,
            actor_id=actor_id,
            actor_role=actor_role,
            notes=notes,
            event_metadata=metadata or {}
        )
        db.add(event)
        await db.commit()
        return event

    @classmethod
    async def assign_officer(
        cls,
        db: AsyncSession,
        complaint_uuid: uuid.UUID,
        officer_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
        actor_role: str | None = 'admin'
    ) -> RoadIssue:
        """Assign an issue to a field officer, calculate SLA, update status, log event."""
        # 1. Fetch officer
        officer_stmt = select(Officer).where(Officer.id == officer_id)
        officer = (await db.execute(officer_stmt)).scalar_one_or_none()
        if not officer:
            msg = f"Officer with ID {officer_id} not found"
            raise ValueError(msg)

        # 2. Fetch issue to know current status
        stmt = select(RoadIssue).where(RoadIssue.uuid == complaint_uuid)
        issue = (await db.execute(stmt)).scalar_one_or_none()
        if not issue:
            msg = f"Complaint with UUID {complaint_uuid} not found"
            raise ValueError(msg)

        # Set officer and SLA details
        issue.assigned_officer_id = officer_id
        issue.sla_deadline = cls.calculate_sla_deadline(issue.severity)
        if officer.department:
            issue.department = officer.department
        await db.commit()

        # Determine target state transition
        target_status = 'assigned'
        if issue.status == 'open':
            # transition first to acknowledged or assigned
            target_status = 'assigned'
        elif issue.status == 'reopened' or issue.status == 'acknowledged':
            target_status = 'assigned'

        # 3. Transition via State Machine
        result = await ComplaintStateMachine.transition(
            db,
            complaint_uuid=complaint_uuid,
            target_status=target_status,
            actor_id=actor_id,
            actor_role=actor_role,
            notes=f"Assigned to officer {officer.name} ({officer.department})",
            metadata={
                "officer_name": officer.name,
                "officer_department": officer.department,
                "sla_deadline": issue.sla_deadline.isoformat() if issue.sla_deadline else None
            }
        )

        return result.issue

    @classmethod
    async def update_status(
        cls,
        db: AsyncSession,
        complaint_uuid: uuid.UUID,
        status: str,
        notes: str | None = None,
        actor_id: uuid.UUID | None = None,
        actor_role: str | None = None
    ) -> RoadIssue:
        """Update complaint status and record audit trail event via state machine."""
        result = await ComplaintStateMachine.transition(
            db,
            complaint_uuid=complaint_uuid,
            target_status=status,
            actor_id=actor_id,
            actor_role=actor_role,
            notes=notes,
        )
        return result.issue

    @classmethod
    async def resolve(
        cls,
        db: AsyncSession,
        complaint_uuid: uuid.UUID,
        after_photo_url: str | None = None,
        notes: str | None = None,
        actor_id: uuid.UUID | None = None,
        actor_role: str | None = 'field_officer'
    ) -> RoadIssue:
        """Mark issue as resolved, record resolution photo, save event via state machine."""
        # Update resolved fields first
        stmt = select(RoadIssue).where(RoadIssue.uuid == complaint_uuid)
        issue = (await db.execute(stmt)).scalar_one_or_none()
        if not issue:
            msg = f"Complaint with UUID {complaint_uuid} not found"
            raise ValueError(msg)

        if after_photo_url:
            issue.after_photo_url = after_photo_url
        await db.commit()

        result = await ComplaintStateMachine.transition(
            db,
            complaint_uuid=complaint_uuid,
            target_status='resolved',
            actor_id=actor_id,
            actor_role=actor_role,
            notes=notes or "Issue resolved by field team.",
            metadata={"after_photo_url": after_photo_url}
        )
        return result.issue

    @classmethod
    async def citizen_confirm(
        cls,
        db: AsyncSession,
        complaint_uuid: uuid.UUID,
        rating: int | None = None,
        notes: str | None = None,
        actor_id: uuid.UUID | None = None
    ) -> RoadIssue:
        """Citizen confirms resolution, closes the complaint."""
        stmt = select(RoadIssue).where(RoadIssue.uuid == complaint_uuid)
        issue = (await db.execute(stmt)).scalar_one_or_none()
        if not issue:
            msg = f"Complaint with UUID {complaint_uuid} not found"
            raise ValueError(msg)

        if rating is not None:
            issue.citizen_rating = rating
        await db.commit()

        # Transition to citizen_confirmed (which automatically leads to closed state transition next, or acts as closed)
        await ComplaintStateMachine.transition(
            db,
            complaint_uuid=complaint_uuid,
            target_status='citizen_confirmed',
            actor_id=actor_id,
            actor_role='citizen',
            notes=notes or f"Citizen confirmed resolution. Rating: {rating or 'Not rated'}",
            metadata={"citizen_rating": rating}
        )

        # Transition to closed terminal state
        closed_result = await ComplaintStateMachine.transition(
            db,
            complaint_uuid=complaint_uuid,
            target_status='closed',
            actor_id=actor_id,
            actor_role='system',
            notes="System closed complaint automatically after citizen confirmation.",
        )
        return closed_result.issue

    @classmethod
    async def citizen_reject(
        cls,
        db: AsyncSession,
        complaint_uuid: uuid.UUID,
        reason: str,
        actor_id: uuid.UUID | None = None
    ) -> RoadIssue:
        """Citizen rejects resolution, reopens and escalates the complaint."""
        stmt = select(RoadIssue).where(RoadIssue.uuid == complaint_uuid)
        issue = (await db.execute(stmt)).scalar_one_or_none()
        if not issue:
            msg = f"Complaint with UUID {complaint_uuid} not found"
            raise ValueError(msg)

        # Set rejection reason
        issue.rejection_reason = reason
        await db.commit()

        # 1. Transition to citizen_rejected
        await ComplaintStateMachine.transition(
            db,
            complaint_uuid=complaint_uuid,
            target_status='citizen_rejected',
            actor_id=actor_id,
            actor_role='citizen',
            notes=f"Citizen rejected resolution. Reason: {reason}",
            metadata={"rejection_reason": reason}
        )

        # 2. Transition to reopened (which auto-bumps severity and resets SLA)
        reopened_result = await ComplaintStateMachine.transition(
            db,
            complaint_uuid=complaint_uuid,
            target_status='reopened',
            actor_id=actor_id,
            actor_role='system',
            notes="Auto-reopened and escalated due to citizen rejection.",
        )

        return reopened_result.issue

    @classmethod
    async def escalate(
        cls,
        db: AsyncSession,
        complaint_uuid: uuid.UUID,
        reason: str,
        escalation_tier: int | None = None,
        actor_id: uuid.UUID | None = None,
        actor_role: str | None = 'system'
    ) -> RoadIssue:
        """Escalate an issue and log event via state machine."""
        result = await ComplaintStateMachine.escalate(
            db,
            complaint_uuid=complaint_uuid,
            reason=reason,
            escalation_tier=escalation_tier,
            actor_id=actor_id,
            actor_role=actor_role,
        )
        return result.issue

    @staticmethod
    async def get_timeline(db: AsyncSession, complaint_uuid: uuid.UUID) -> list[ComplaintEvent]:
        """Get the chronological audit log of all events for this issue."""
        stmt = (
            select(ComplaintEvent)
            .where(ComplaintEvent.complaint_uuid == complaint_uuid)
            .order_by(ComplaintEvent.created_at.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
