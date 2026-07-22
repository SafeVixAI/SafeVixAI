# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.complaint_state_machine import (
    ComplaintStateMachine,
    InvalidTransitionError,
)


class TestCanTransition:
    def test_open_to_acknowledged(self):
        assert ComplaintStateMachine.can_transition("open", "acknowledged") is True

    def test_open_to_rejected(self):
        assert ComplaintStateMachine.can_transition("open", "rejected") is True

    def test_resolved_to_citizen_confirmed(self):
        assert ComplaintStateMachine.can_transition("resolved", "citizen_confirmed") is True

    def test_closed_is_terminal(self):
        assert ComplaintStateMachine.can_transition("closed", "open") is False

    def test_rejected_is_terminal(self):
        assert ComplaintStateMachine.can_transition("rejected", "open") is False

    def test_invalid_skip(self):
        assert ComplaintStateMachine.can_transition("open", "resolved") is False

    def test_unknown_state(self):
        assert ComplaintStateMachine.can_transition("nonexistent", "open") is False

    def test_pending_review_to_open(self):
        assert ComplaintStateMachine.can_transition("pending_review", "open") is True

    def test_citizen_rejected_to_reopened(self):
        assert ComplaintStateMachine.can_transition("citizen_rejected", "reopened") is True

    def test_reopened_to_assigned(self):
        assert ComplaintStateMachine.can_transition("reopened", "assigned") is True


class TestGetAllowedTransitions:
    def test_open_transitions_sorted(self):
        t = ComplaintStateMachine.get_allowed_transitions("open")
        assert t == ["acknowledged", "assigned", "pending_review", "rejected"]

    def test_closed_empty(self):
        assert ComplaintStateMachine.get_allowed_transitions("closed") == []

    def test_rejected_empty(self):
        assert ComplaintStateMachine.get_allowed_transitions("rejected") == []

    def test_assigned_transitions(self):
        t = ComplaintStateMachine.get_allowed_transitions("assigned")
        assert "accepted" in t
        assert "reassigned" in t

    def test_resolved_transitions(self):
        t = ComplaintStateMachine.get_allowed_transitions("resolved")
        assert "citizen_confirmed" in t
        assert "citizen_rejected" in t


class TestTransition:
    @pytest.fixture
    def db(self):
        db = MagicMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def issue(self):
        issue = MagicMock()
        issue.uuid = uuid.uuid4()
        issue.status = "open"
        issue.complaint_ref = "REF-TEST"
        issue.severity = 3
        issue.ward_id = "WARD-1"
        issue.category = "roads"
        issue.assigned_officer_id = None
        issue.reopen_count = 0
        return issue

    async def test_transition_open_to_acknowledged(self, db, issue):
        result = MagicMock()
        result.scalar_one_or_none.return_value = issue
        db.execute.return_value = result

        res = await ComplaintStateMachine.transition(
            db, complaint_uuid=issue.uuid, target_status="acknowledged",
            actor_id=uuid.uuid4(), actor_role="admin",
        )
        assert res.success is True
        assert res.old_status == "open"
        assert res.new_status == "acknowledged"
        assert issue.status == "acknowledged"
        db.commit.assert_awaited()
        db.refresh.assert_awaited_with(issue)

    async def test_transition_invalid_raises(self, db, issue):
        result = MagicMock()
        result.scalar_one_or_none.return_value = issue
        db.execute.return_value = result

        with pytest.raises(InvalidTransitionError):
            await ComplaintStateMachine.transition(
                db, complaint_uuid=issue.uuid, target_status="resolved",
            )

    async def test_transition_not_found(self, db):
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute.return_value = result

        with pytest.raises(ValueError, match="not found"):
            await ComplaintStateMachine.transition(
                db, complaint_uuid=uuid.uuid4(), target_status="assigned",
            )

    async def test_transition_sets_accepted_fields(self, db, issue):
        issue.status = "assigned"
        result = MagicMock()
        result.scalar_one_or_none.return_value = issue
        db.execute.return_value = result
        actor_id = uuid.uuid4()

        res = await ComplaintStateMachine.transition(
            db, complaint_uuid=issue.uuid, target_status="accepted",
            actor_id=actor_id,
        )
        assert res.success is True
        assert issue.accepted_at is not None
        assert issue.accepted_by == actor_id

    async def test_transition_sets_resolved_at(self, db, issue):
        issue.status = "in_progress"
        result = MagicMock()
        result.scalar_one_or_none.return_value = issue
        db.execute.return_value = result

        res = await ComplaintStateMachine.transition(
            db, complaint_uuid=issue.uuid, target_status="resolved",
        )
        assert res.success is True
        assert issue.resolved_at is not None

    async def test_transition_reopened_bumps_severity(self, db, issue):
        issue.status = "citizen_rejected"
        issue.severity = 3
        result = MagicMock()
        result.scalar_one_or_none.return_value = issue
        db.execute.return_value = result

        with patch("services.complaint_lifecycle.ComplaintLifecycle.calculate_sla_deadline") as mock_sla:
            mock_sla.return_value = "2026-02-01"
            res = await ComplaintStateMachine.transition(
                db, complaint_uuid=issue.uuid, target_status="reopened",
            )
        assert res.success is True
        assert issue.severity == 4

    async def test_transition_field_updates_in_progress(self, db, issue):
        issue.status = "accepted"
        result = MagicMock()
        result.scalar_one_or_none.return_value = issue
        db.execute.return_value = result

        res = await ComplaintStateMachine.transition(
            db, complaint_uuid=issue.uuid, target_status="in_progress",
        )
        assert res.success is True
        assert issue.work_started_at is not None

    async def test_transition_resolved_field(self, db, issue):
        issue.status = "citizen_confirmed"
        result = MagicMock()
        result.scalar_one_or_none.return_value = issue
        db.execute.return_value = result

        res = await ComplaintStateMachine.transition(
            db, complaint_uuid=issue.uuid, target_status="closed",
        )
        assert res.success is True


class TestEscalate:
    @pytest.fixture
    def db(self):
        db = MagicMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def issue(self):
        issue = MagicMock()
        issue.uuid = uuid.uuid4()
        issue.status = "acknowledged"
        issue.complaint_ref = "REF-ESC"
        issue.severity = 3
        issue.escalation_tier = 0
        issue.ward_id = "WARD-1"
        issue.assigned_officer_id = None
        return issue

    async def test_escalate_bumps_severity_and_tier(self, db, issue):
        result = MagicMock()
        result.scalar_one_or_none.return_value = issue
        db.execute.return_value = result

        res = await ComplaintStateMachine.escalate(
            db, complaint_uuid=issue.uuid, reason="Citizen requested escalation",
            actor_role="citizen",
        )
        assert res.success is True
        assert issue.severity == 4
        assert issue.escalation_tier == 1

    async def test_escalate_with_custom_tier(self, db, issue):
        result = MagicMock()
        result.scalar_one_or_none.return_value = issue
        db.execute.return_value = result

        await ComplaintStateMachine.escalate(
            db, complaint_uuid=issue.uuid, reason="Direct escalation to tier 3",
            escalation_tier=3, actor_id=uuid.uuid4(), actor_role="admin",
        )
        assert issue.escalation_tier == 3

    async def test_escalate_at_max_severity(self, db, issue):
        issue.severity = 5
        result = MagicMock()
        result.scalar_one_or_none.return_value = issue
        db.execute.return_value = result

        await ComplaintStateMachine.escalate(
            db, complaint_uuid=issue.uuid, reason="Already max severity",
        )
        assert issue.severity == 5

    async def test_escalate_not_found(self, db):
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute.return_value = result

        with pytest.raises(ValueError, match="not found"):
            await ComplaintStateMachine.escalate(
                db, complaint_uuid=uuid.uuid4(), reason="not found",
            )
