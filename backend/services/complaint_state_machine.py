# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Issue state machine for SafeVixAI.

Domain language: "issue" (RoadIssue) = road condition report.
State machine manages RoadIssue lifecycle transitions with full audit trail.

State Diagram:
    open ──→ pending_review (low AI confidence)
    open ──→ acknowledged (duplicate linked OR auto-assigned)
    open ──→ rejected (spam/fake detected)
    pending_review ──→ open (human approved)
    pending_review ──→ rejected (human rejected)
    acknowledged ──→ assigned (officer assigned)
    assigned ──→ accepted (officer accepts)
    assigned ──→ reassigned (officer rejects → routes to another)
    reassigned ──→ assigned (new officer assigned)
    accepted ──→ in_progress (field work started)
    in_progress ──→ resolved (work completed with evidence)
    resolved ──→ citizen_confirmed (citizen verified)
    resolved ──→ citizen_rejected (citizen disputes)
    citizen_confirmed ──→ closed (final state)
    citizen_rejected ──→ reopened (auto-escalate)
    reopened ──→ assigned (re-routed with higher severity)

    Any active → escalated (severity bump, stays in current status)
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.complaint_event import ComplaintEvent
from models.road_issue import RoadIssue
from services.event_bus import DomainEvent, get_event_bus

logger = logging.getLogger("safevixai.state_machine")


class InvalidTransitionError(Exception):
    """Raised when a complaint status transition is not allowed."""
    def __init__(self, current_status: str, target_status: str, complaint_ref: str | None = None):
        self.current_status = current_status
        self.target_status = target_status
        msg = f"Invalid transition: {current_status} → {target_status}"
        if complaint_ref:
            msg += f" (complaint: {complaint_ref})"
        super().__init__(msg)


# Valid transitions: current_status → set of allowed target statuses
VALID_TRANSITIONS: dict[str, set[str]] = {
    "open": {"pending_review", "acknowledged", "assigned", "rejected"},
    "pending_review": {"open", "acknowledged", "rejected"},
    "acknowledged": {"assigned", "rejected"},
    "assigned": {"accepted", "reassigned", "in_progress"},  # in_progress for backward compat
    "reassigned": {"assigned"},
    "accepted": {"in_progress"},
    "in_progress": {"resolved"},
    "resolved": {"citizen_confirmed", "citizen_rejected", "closed"},
    "citizen_confirmed": {"closed"},
    "citizen_rejected": {"reopened"},
    "reopened": {"assigned"},
    "closed": set(),  # Terminal state
    "rejected": set(),  # Terminal state
}

# Event types emitted per transition
TRANSITION_EVENT_MAP: dict[str, str] = {
    "open": "complaint.created",
    "pending_review": "complaint.pending_review",
    "acknowledged": "complaint.acknowledged",
    "assigned": "complaint.assigned",
    "reassigned": "complaint.rejected_by_authority",
    "accepted": "complaint.accepted",
    "in_progress": "complaint.work_started",
    "resolved": "complaint.resolved",
    "citizen_confirmed": "complaint.citizen_confirmed",
    "citizen_rejected": "complaint.citizen_rejected",
    "reopened": "complaint.reopened",
    "closed": "complaint.closed",
    "rejected": "complaint.rejected",
    "escalated": "complaint.escalated",
}


@dataclass
class TransitionResult:
    """Result of a state transition."""
    success: bool
    old_status: str
    new_status: str
    event: ComplaintEvent | None
    domain_event: DomainEvent | None
    issue: RoadIssue | None


class ComplaintStateMachine:
    """Enforces valid complaint state transitions with full audit trail."""

    @staticmethod
    def can_transition(current_status: str, target_status: str) -> bool:
        """Check if a transition is valid without performing it."""
        allowed = VALID_TRANSITIONS.get(current_status, set())
        return target_status in allowed

    @staticmethod
    def get_allowed_transitions(current_status: str) -> list[str]:
        """Get all valid next states from the current state."""
        return sorted(VALID_TRANSITIONS.get(current_status, set()))

    @classmethod
    async def transition(
        cls,
        db: AsyncSession,
        *,
        complaint_uuid: uuid.UUID,
        target_status: str,
        actor_id: uuid.UUID | None = None,
        actor_role: str | None = None,
        notes: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TransitionResult:
        """
        Perform a validated state transition.

        - Validates the transition is allowed
        - Updates the issue status
        - Creates audit trail event
        - Publishes domain event to the event bus
        - Returns TransitionResult with full context
        """
        # 1. Fetch the issue
        stmt = select(RoadIssue).where(RoadIssue.uuid == complaint_uuid)
        issue = (await db.execute(stmt)).scalar_one_or_none()
        if not issue:
            msg = f"Complaint with UUID {complaint_uuid} not found"
            raise ValueError(msg)

        old_status = issue.status

        # 2. Validate transition
        if not cls.can_transition(old_status, target_status):
            raise InvalidTransitionError(old_status, target_status, issue.complaint_ref)

        # 3. Update status
        now = datetime.now(UTC).replace(tzinfo=None)
        issue.status = target_status
        issue.status_updated = now

        # Status-specific field updates
        if target_status == "accepted":
            issue.accepted_at = now
            if actor_id:
                issue.accepted_by = actor_id
        elif target_status == "in_progress":
            issue.work_started_at = now
        elif target_status == "resolved":
            issue.resolved_at = now
        elif target_status == "citizen_confirmed":
            issue.citizen_confirmed_at = now
        elif target_status == "citizen_rejected":
            issue.reopen_count = (issue.reopen_count or 0) + 1
        elif target_status == "reopened":
            # Auto-escalate: increase severity
            if issue.severity < 5:
                issue.severity += 1
            # Reset SLA with new severity
            from services.complaint_lifecycle import ComplaintLifecycle
            issue.sla_deadline = ComplaintLifecycle.calculate_sla_deadline(issue.severity)

        await db.commit()
        await db.refresh(issue)

        # 4. Create audit trail event
        event = ComplaintEvent(
            complaint_uuid=complaint_uuid,
            event_type=target_status,
            actor_id=actor_id,
            actor_role=actor_role,
            notes=notes or f"Status changed: {old_status} → {target_status}",
            event_metadata={
                **(metadata or {}),
                "old_status": old_status,
                "new_status": target_status,
                "transition_timestamp": now.isoformat(),
            },
        )
        db.add(event)
        await db.commit()

        # 5. Publish domain event
        event_type = TRANSITION_EVENT_MAP.get(target_status, f"complaint.{target_status}")
        domain_event = DomainEvent.create(
            event_type=event_type,
            payload={
                "complaint_uuid": str(complaint_uuid),
                "complaint_ref": issue.complaint_ref,
                "old_status": old_status,
                "new_status": target_status,
                "severity": issue.severity,
                "ward_id": issue.ward_id,
                "category": issue.category,
                "assigned_officer_id": str(issue.assigned_officer_id) if issue.assigned_officer_id else None,
            },
            correlation_id=str(complaint_uuid),
            actor_id=str(actor_id) if actor_id else None,
            actor_role=actor_role,
        )

        try:
            bus = get_event_bus()
            await bus.publish(domain_event)
        except Exception as e:
            logger.error("Failed to publish domain event: %s", e)

        logger.info(
            "Transition: %s → %s for %s by %s",
            old_status, target_status, issue.complaint_ref, actor_role or "system",
        )

        return TransitionResult(
            success=True,
            old_status=old_status,
            new_status=target_status,
            event=event,
            domain_event=domain_event,
            issue=issue,
        )

    @classmethod
    async def escalate(
        cls,
        db: AsyncSession,
        *,
        complaint_uuid: uuid.UUID,
        reason: str,
        escalation_tier: int | None = None,
        actor_id: uuid.UUID | None = None,
        actor_role: str | None = None,
    ) -> TransitionResult:
        """
        Escalate a complaint without changing its status.
        Increases severity and escalation tier.
        """
        stmt = select(RoadIssue).where(RoadIssue.uuid == complaint_uuid)
        issue = (await db.execute(stmt)).scalar_one_or_none()
        if not issue:
            msg = f"Complaint with UUID {complaint_uuid} not found"
            raise ValueError(msg)

        old_severity = issue.severity
        old_tier = getattr(issue, 'escalation_tier', 0) or 0

        # Bump severity
        if issue.severity < 5:
            issue.severity += 1

        # Bump escalation tier
        new_tier = escalation_tier if escalation_tier is not None else old_tier + 1
        if hasattr(issue, 'escalation_tier'):
            issue.escalation_tier = new_tier

        now = datetime.now(UTC).replace(tzinfo=None)
        issue.status_updated = now

        await db.commit()
        await db.refresh(issue)

        # Audit event
        event = ComplaintEvent(
            complaint_uuid=complaint_uuid,
            event_type="escalated",
            actor_id=actor_id,
            actor_role=actor_role or "system",
            notes=reason,
            event_metadata={
                "old_severity": old_severity,
                "new_severity": issue.severity,
                "old_tier": old_tier,
                "new_tier": new_tier,
                "reason": reason,
            },
        )
        db.add(event)
        await db.commit()

        # Domain event
        domain_event = DomainEvent.create(
            event_type="complaint.escalated",
            payload={
                "complaint_uuid": str(complaint_uuid),
                "complaint_ref": issue.complaint_ref,
                "old_severity": old_severity,
                "new_severity": issue.severity,
                "escalation_tier": new_tier,
                "reason": reason,
                "status": issue.status,
            },
            correlation_id=str(complaint_uuid),
            actor_id=str(actor_id) if actor_id else None,
            actor_role=actor_role,
        )

        try:
            bus = get_event_bus()
            await bus.publish(domain_event)
        except Exception as e:
            logger.error("Failed to publish escalation event: %s", e)

        return TransitionResult(
            success=True,
            old_status=issue.status,
            new_status=issue.status,
            event=event,
            domain_event=domain_event,
            issue=issue,
        )
