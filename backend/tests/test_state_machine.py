# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.complaint_state_machine import ComplaintStateMachine, InvalidTransitionError


def test_can_transition():
    # Valid transitions
    assert ComplaintStateMachine.can_transition("open", "assigned") is True
    assert ComplaintStateMachine.can_transition("assigned", "accepted") is True
    assert ComplaintStateMachine.can_transition("accepted", "in_progress") is True
    assert ComplaintStateMachine.can_transition("in_progress", "resolved") is True

    # Invalid transitions
    assert ComplaintStateMachine.can_transition("open", "resolved") is False
    assert ComplaintStateMachine.can_transition("closed", "open") is False


def test_get_allowed_transitions():
    transitions = ComplaintStateMachine.get_allowed_transitions("open")
    assert "assigned" in transitions
    assert "pending_review" in transitions
    assert "rejected" in transitions


@pytest.mark.asyncio
async def test_transition_success():
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()

    issue = MagicMock()
    issue.uuid = uuid.uuid4()
    issue.status = "open"
    issue.complaint_ref = "REF-1234"
    issue.severity = 3
    issue.ward_id = "WARD-1"
    issue.category = "roads"
    issue.assigned_officer_id = None

    result = MagicMock()
    result.scalar_one_or_none.return_value = issue
    db.execute.return_value = result

    # Perform valid transition: open -> assigned
    res = await ComplaintStateMachine.transition(
        db,
        complaint_uuid=issue.uuid,
        target_status="assigned",
        actor_id=uuid.uuid4(),
        actor_role="admin",
        notes="Assigning complaint to officer"
    )

    assert res.success is True
    assert res.old_status == "open"
    assert res.new_status == "assigned"
    assert issue.status == "assigned"
    db.commit.assert_awaited()
    db.refresh.assert_awaited_once_with(issue)


@pytest.mark.asyncio
async def test_invalid_transition_raises_error():
    db = MagicMock()
    db.execute = AsyncMock()

    issue = MagicMock()
    issue.uuid = uuid.uuid4()
    issue.status = "open"
    issue.complaint_ref = "REF-1234"

    result = MagicMock()
    result.scalar_one_or_none.return_value = issue
    db.execute.return_value = result

    # Perform invalid transition: open -> resolved
    with pytest.raises(InvalidTransitionError):
        await ComplaintStateMachine.transition(
            db,
            complaint_uuid=issue.uuid,
            target_status="resolved"
        )
