# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.complaint_state_machine import ComplaintStateMachine


@pytest.mark.asyncio
async def test_escalation_increases_severity():
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()

    issue = MagicMock()
    issue.uuid = uuid.uuid4()
    issue.status = "assigned"
    issue.complaint_ref = "REF-9999"
    issue.severity = 3
    issue.escalation_tier = 0

    result = MagicMock()
    result.scalar_one_or_none.return_value = issue
    db.execute.return_value = result

    # Perform escalation
    res = await ComplaintStateMachine.escalate(
        db,
        complaint_uuid=issue.uuid,
        reason="Assigned officer did not respond",
        escalation_tier=1
    )

    assert res.success is True
    assert issue.severity == 4
    assert issue.escalation_tier == 1
    db.commit.assert_awaited()
    db.refresh.assert_awaited_once_with(issue)
