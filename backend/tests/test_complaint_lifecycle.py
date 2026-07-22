# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.complaint_lifecycle import ComplaintLifecycle

FROZEN = datetime(2026, 5, 23, 10, 0, 0)


class TestCalculateSLADeadline:
    def test_severity_5_extreme_4_hours(self):
        with patch('services.complaint_lifecycle.datetime') as mock_dt:
            mock_dt.now.return_value = FROZEN.replace(tzinfo=UTC)
            deadline = ComplaintLifecycle.calculate_sla_deadline(5)
        assert deadline == FROZEN + timedelta(hours=4)

    def test_severity_4_critical_24_hours(self):
        with patch('services.complaint_lifecycle.datetime') as mock_dt:
            mock_dt.now.return_value = FROZEN.replace(tzinfo=UTC)
            deadline = ComplaintLifecycle.calculate_sla_deadline(4)
        assert deadline == FROZEN + timedelta(hours=24)

    def test_severity_3_serious_72_hours(self):
        with patch('services.complaint_lifecycle.datetime') as mock_dt:
            mock_dt.now.return_value = FROZEN.replace(tzinfo=UTC)
            deadline = ComplaintLifecycle.calculate_sla_deadline(3)
        assert deadline == FROZEN + timedelta(hours=72)

    def test_severity_1_or_2_seven_days(self):
        for sev in (1, 2):
            with patch('services.complaint_lifecycle.datetime') as mock_dt:
                mock_dt.now.return_value = FROZEN.replace(tzinfo=UTC)
                deadline = ComplaintLifecycle.calculate_sla_deadline(sev)
            assert deadline == FROZEN + timedelta(days=7)

    def test_severity_0_defaults_seven_days(self):
        with patch('services.complaint_lifecycle.datetime') as mock_dt:
            mock_dt.now.return_value = FROZEN.replace(tzinfo=UTC)
            deadline = ComplaintLifecycle.calculate_sla_deadline(0)
        assert deadline == FROZEN + timedelta(days=7)


class TestLogEvent:
    @pytest.mark.asyncio
    async def test_log_event_creates_and_commits_event(self):
        db = MagicMock()
        db.commit = AsyncMock()
        db.add = MagicMock()

        complaint_uuid = uuid.uuid4()
        actor_id = uuid.uuid4()

        event = await ComplaintLifecycle.log_event(
            db,
            complaint_uuid=complaint_uuid,
            event_type="assigned",
            actor_id=actor_id,
            actor_role="admin",
            notes="Test event notes",
            metadata={"key": "value"},
        )

        assert event.complaint_uuid == complaint_uuid
        assert event.event_type == "assigned"
        assert event.actor_id == actor_id
        assert event.actor_role == "admin"
        assert event.notes == "Test event notes"
        db.add.assert_called_once()
        arg = db.add.call_args[0][0]
        assert arg.complaint_uuid == complaint_uuid
        db.commit.assert_awaited_once()


class TestAssignOfficer:
    def _setup_mocks(self, status="open"):
        db = MagicMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()

        issue = MagicMock()
        issue.uuid = uuid.uuid4()
        issue.severity = 3
        issue.status = status
        issue.complaint_ref = f"REF-{status}"
        issue.assigned_officer_id = None
        issue.sla_deadline = None

        officer = MagicMock()
        officer.name = "Ravi Kumar"
        officer.department = "Traffic Police"

        return db, issue, officer

    @pytest.mark.asyncio
    async def test_assign_officer_success(self):
        db, issue, officer = self._setup_mocks("open")

        async def mock_exec(stmt):
            stmt_str = str(stmt).lower()
            res = MagicMock()
            if "from officers" in stmt_str:
                res.scalar_one_or_none.return_value = officer
            else:
                res.scalar_one_or_none.return_value = issue
            return res

        db.execute.side_effect = mock_exec

        result = await ComplaintLifecycle.assign_officer(
            db,
            complaint_uuid=issue.uuid,
            officer_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            actor_role="admin",
        )

        assert result.assigned_officer_id is not None

    @pytest.mark.asyncio
    async def test_assign_officer_from_reopened_status(self):
        db, issue, officer = self._setup_mocks("reopened")

        async def mock_exec(stmt):
            stmt_str = str(stmt).lower()
            res = MagicMock()
            if "from officers" in stmt_str:
                res.scalar_one_or_none.return_value = officer
            else:
                res.scalar_one_or_none.return_value = issue
            return res

        db.execute.side_effect = mock_exec

        result = await ComplaintLifecycle.assign_officer(
            db,
            complaint_uuid=issue.uuid,
            officer_id=uuid.uuid4(),
        )

        assert result.assigned_officer_id is not None

    @pytest.mark.asyncio
    async def test_assign_officer_from_acknowledged_status(self):
        db, issue, officer = self._setup_mocks("acknowledged")

        async def mock_exec(stmt):
            stmt_str = str(stmt).lower()
            res = MagicMock()
            if "from officers" in stmt_str:
                res.scalar_one_or_none.return_value = officer
            else:
                res.scalar_one_or_none.return_value = issue
            return res

        db.execute.side_effect = mock_exec

        result = await ComplaintLifecycle.assign_officer(
            db,
            complaint_uuid=issue.uuid,
            officer_id=uuid.uuid4(),
        )

        assert result.assigned_officer_id is not None

    @pytest.mark.asyncio
    async def test_assign_officer_officer_not_found(self):
        db = MagicMock()
        db.execute = AsyncMock()

        async def mock_exec(stmt):
            res = MagicMock()
            res.scalar_one_or_none.return_value = None
            return res

        db.execute.side_effect = mock_exec

        with pytest.raises(ValueError, match="Officer with ID"):
            await ComplaintLifecycle.assign_officer(
                db, complaint_uuid=uuid.uuid4(), officer_id=uuid.uuid4()
            )

    @pytest.mark.asyncio
    async def test_assign_officer_issue_not_found(self):
        db = MagicMock()
        db.execute = AsyncMock()
        officer = MagicMock()
        officer.name = "Ravi"
        officer.department = "Traffic"

        async def mock_exec(stmt):
            stmt_str = str(stmt).lower()
            res = MagicMock()
            if "from officers" in stmt_str:
                res.scalar_one_or_none.return_value = officer
            else:
                res.scalar_one_or_none.return_value = None
            return res

        db.execute.side_effect = mock_exec

        with pytest.raises(ValueError, match="Complaint with UUID"):
            await ComplaintLifecycle.assign_officer(
                db, complaint_uuid=uuid.uuid4(), officer_id=uuid.uuid4()
            )


class TestUpdateStatus:
    @pytest.mark.asyncio
    async def test_update_status_success(self):
        db = MagicMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()

        issue = MagicMock()
        issue.status = "open"
        issue.uuid = uuid.uuid4()
        issue.complaint_ref = "REF-123"

        result = MagicMock()
        result.scalar_one_or_none.return_value = issue
        db.execute.return_value = result

        updated = await ComplaintLifecycle.update_status(
            db,
            complaint_uuid=issue.uuid,
            status="assigned",
            actor_id=uuid.uuid4(),
            actor_role="field_officer",
        )

        assert updated.status == "assigned"

    @pytest.mark.asyncio
    async def test_update_status_issue_not_found(self):
        db = MagicMock()
        db.execute = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute.return_value = result

        with pytest.raises(ValueError, match="Complaint with UUID"):
            await ComplaintLifecycle.update_status(
                db, complaint_uuid=uuid.uuid4(), status="resolved"
            )


class TestResolve:
    @pytest.mark.asyncio
    async def test_resolve_with_photo(self):
        db = MagicMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()

        issue = MagicMock()
        issue.uuid = uuid.uuid4()
        issue.status = "in_progress"
        issue.complaint_ref = "REF-123"
        issue.after_photo_url = None

        result = MagicMock()
        result.scalar_one_or_none.return_value = issue
        db.execute.return_value = result

        resolved = await ComplaintLifecycle.resolve(
            db,
            complaint_uuid=issue.uuid,
            after_photo_url="https://example.com/photo.jpg",
        )

        assert resolved.after_photo_url == "https://example.com/photo.jpg"

    @pytest.mark.asyncio
    async def test_resolve_without_photo(self):
        db = MagicMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()

        issue = MagicMock()
        issue.uuid = uuid.uuid4()
        issue.status = "in_progress"
        issue.complaint_ref = "REF-123"
        issue.after_photo_url = None

        result = MagicMock()
        result.scalar_one_or_none.return_value = issue
        db.execute.return_value = result

        resolved = await ComplaintLifecycle.resolve(
            db, complaint_uuid=issue.uuid
        )

        assert resolved.after_photo_url is None

    @pytest.mark.asyncio
    async def test_resolve_issue_not_found(self):
        db = MagicMock()
        db.execute = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute.return_value = result

        with pytest.raises(ValueError, match="Complaint with UUID"):
            await ComplaintLifecycle.resolve(db, complaint_uuid=uuid.uuid4())


class TestCitizenConfirm:
    @pytest.mark.asyncio
    async def test_citizen_confirm_success_with_rating(self):
        db = MagicMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()

        issue = MagicMock()
        issue.uuid = uuid.uuid4()
        issue.status = "resolved"
        issue.complaint_ref = "REF-123"
        issue.citizen_rating = None

        result = MagicMock()
        result.scalar_one_or_none.return_value = issue
        db.execute.return_value = result

        closed = await ComplaintLifecycle.citizen_confirm(
            db,
            complaint_uuid=issue.uuid,
            rating=5,
            actor_id=uuid.uuid4(),
        )

        assert closed.status == "closed"

    @pytest.mark.asyncio
    async def test_citizen_confirm_without_rating(self):
        db = MagicMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()

        issue = MagicMock()
        issue.uuid = uuid.uuid4()
        issue.status = "resolved"
        issue.complaint_ref = "REF-456"

        result = MagicMock()
        result.scalar_one_or_none.return_value = issue
        db.execute.return_value = result

        closed = await ComplaintLifecycle.citizen_confirm(
            db, complaint_uuid=issue.uuid
        )

        assert closed.status == "closed"

    @pytest.mark.asyncio
    async def test_citizen_confirm_issue_not_found(self):
        db = MagicMock()
        db.execute = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute.return_value = result

        with pytest.raises(ValueError, match="Complaint with UUID"):
            await ComplaintLifecycle.citizen_confirm(
                db, complaint_uuid=uuid.uuid4()
            )


class TestCitizenReject:
    @pytest.mark.asyncio
    async def test_citizen_reject_success(self):
        db = MagicMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()

        issue = MagicMock()
        issue.uuid = uuid.uuid4()
        issue.status = "resolved"
        issue.complaint_ref = "REF-789"
        issue.rejection_reason = None
        issue.severity = 3

        result = MagicMock()
        result.scalar_one_or_none.return_value = issue
        db.execute.return_value = result

        reopened = await ComplaintLifecycle.citizen_reject(
            db,
            complaint_uuid=issue.uuid,
            reason="Work was not done properly",
            actor_id=uuid.uuid4(),
        )

        assert reopened.status == "reopened"

    @pytest.mark.asyncio
    async def test_citizen_reject_issue_not_found(self):
        db = MagicMock()
        db.execute = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute.return_value = result

        with pytest.raises(ValueError, match="Complaint with UUID"):
            await ComplaintLifecycle.citizen_reject(
                db, complaint_uuid=uuid.uuid4(), reason="Not fixed properly"
            )


class TestEscalate:
    @pytest.mark.asyncio
    async def test_escalate_increases_severity(self):
        db = MagicMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()

        issue = MagicMock()
        issue.uuid = uuid.uuid4()
        issue.severity = 3
        issue.status = "assigned"
        issue.complaint_ref = "REF-123"
        issue.escalation_tier = 0

        result = MagicMock()
        result.scalar_one_or_none.return_value = issue
        db.execute.return_value = result

        escalated = await ComplaintLifecycle.escalate(
            db, complaint_uuid=issue.uuid, reason="SLA breach"
        )

        assert escalated.severity == 4

    @pytest.mark.asyncio
    async def test_escalate_max_severity_stays_five(self):
        db = MagicMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()

        issue = MagicMock()
        issue.uuid = uuid.uuid4()
        issue.severity = 5
        issue.status = "assigned"
        issue.complaint_ref = "REF-123"
        issue.escalation_tier = 0

        result = MagicMock()
        result.scalar_one_or_none.return_value = issue
        db.execute.return_value = result

        escalated = await ComplaintLifecycle.escalate(
            db, complaint_uuid=issue.uuid, reason="Further escalation"
        )

        assert escalated.severity == 5


class TestGetTimeline:
    @pytest.mark.asyncio
    async def test_get_timeline_returns_events(self):
        db = MagicMock()
        db.execute = AsyncMock()

        event1 = MagicMock()
        event1.event_type = "created"
        event2 = MagicMock()
        event2.event_type = "assigned"

        result = MagicMock()
        scalars_result = MagicMock()
        scalars_result.all.return_value = [event1, event2]
        result.scalars.return_value = scalars_result
        db.execute.return_value = result

        timeline = await ComplaintLifecycle.get_timeline(
            db, complaint_uuid=uuid.uuid4()
        )

        assert timeline == [event1, event2]
        assert timeline[0].event_type == "created"
