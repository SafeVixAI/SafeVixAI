# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from services.duplicate_detector import DuplicateDetector


@pytest.fixture
def mock_db():
    db = AsyncMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def sample_issue():
    return MagicMock(
        uuid=uuid.uuid4(),
        status="open",
        issue_type="pothole",
        confirmation_count=2,
        location=None,
        created_at=datetime.utcnow(),
    )


@pytest.mark.asyncio
async def test_find_duplicates_returns_matching_issues(mock_db):
    issue_a = MagicMock(uuid=uuid.uuid4(), status="open", issue_type="pothole")
    issue_b = MagicMock(uuid=uuid.uuid4(), status="acknowledged", issue_type="pothole")
    result = MagicMock()
    result.scalars.return_value.all.return_value = [issue_a, issue_b]
    mock_db.execute.return_value = result

    results = await DuplicateDetector.find_duplicates(
        mock_db, lat=13.0827, lon=80.2707, issue_type="pothole", radius_meters=100
    )

    assert len(results) == 2
    assert results[0] is issue_a
    assert results[1] is issue_b
    mock_db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_find_duplicates_no_duplicates(mock_db):
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = result

    results = await DuplicateDetector.find_duplicates(
        mock_db, lat=13.0827, lon=80.2707, issue_type="pothole", radius_meters=100
    )

    assert results == []


@pytest.mark.asyncio
async def test_increment_confirmation_issue_found(mock_db, sample_issue):
    sample_issue.confirmation_count = 3
    result = MagicMock()
    result.scalar_one_or_none.return_value = sample_issue
    mock_db.execute.return_value = result

    returned = await DuplicateDetector.increment_confirmation(mock_db, sample_issue.uuid)

    assert returned is sample_issue
    assert sample_issue.confirmation_count == 4
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once_with(sample_issue)


@pytest.mark.asyncio
async def test_increment_confirmation_triggers_auto_acknowledge(mock_db, sample_issue):
    sample_issue.status = "open"
    sample_issue.confirmation_count = 4
    result = MagicMock()
    result.scalar_one_or_none.return_value = sample_issue
    mock_db.execute.return_value = result

    returned = await DuplicateDetector.increment_confirmation(mock_db, sample_issue.uuid)

    assert returned is sample_issue
    assert sample_issue.confirmation_count == 5
    assert sample_issue.status == "acknowledged"
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once_with(sample_issue)


@pytest.mark.asyncio
async def test_increment_confirmation_issue_not_found(mock_db):
    issue_uuid = uuid.uuid4()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = result

    returned = await DuplicateDetector.increment_confirmation(mock_db, issue_uuid)

    assert returned is None
    mock_db.commit.assert_not_called()
    mock_db.refresh.assert_not_called()
