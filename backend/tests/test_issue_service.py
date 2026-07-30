# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from models.issue_report import IssueReport
from models.issue_timeline import IssueTimelineEvent
from models.schemas_issues import (
    CreateIssueRequest,
    IssueSeverity,
    IssueStatus,
    IssueType,
    UpdateIssueRequest,
)
from services.issue_service import IssueService


@pytest.fixture
def issue_service() -> IssueService:
    return IssueService()


@pytest.fixture
def create_request() -> CreateIssueRequest:
    return CreateIssueRequest(
        issue_type=IssueType.bug,
        title='Test button not working',
        description='The submit button does nothing when clicked',
        steps_to_reproduce='1. Go to settings\n2. Click Submit\n3. Nothing happens',
        expected_behavior='Form should submit',
        actual_behavior='Nothing happens',
        environment='Chrome 120, Windows 11',
        severity=IssueSeverity.high,
        labels=['frontend', 'ui'],
    )


@pytest.mark.asyncio
async def test_create_issue(issue_service: IssueService, create_request: CreateIssueRequest) -> None:
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    result = await issue_service.create_issue(db=mock_db, request=create_request)

    assert result.title == 'Test button not working'
    assert result.tracking_number.startswith('SAFE-')
    assert result.issue_type == 'bug'
    assert result.status == 'new'
    assert result.is_spam is False
    assert mock_db.add.call_count >= 2


@pytest.mark.asyncio
async def test_create_issue_anonymous(issue_service: IssueService, create_request: CreateIssueRequest) -> None:
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    create_request_anon = create_request.model_copy(update={'is_anonymous': True})

    result = await issue_service.create_issue(db=mock_db, request=create_request_anon)

    assert result.is_anonymous is True
    assert result.reporter_name is None


@pytest.mark.asyncio
async def test_create_issue_with_location(issue_service: IssueService, create_request: CreateIssueRequest) -> None:
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    create_request_loc = create_request.model_copy(update={'lat': 13.0827, 'lon': 80.2707})

    result = await issue_service.create_issue(db=mock_db, request=create_request_loc)

    assert result is not None


@pytest.mark.asyncio
async def test_get_issue(issue_service: IssueService) -> None:
    mock_result = MagicMock()
    mock_issue = MagicMock(spec=IssueReport)
    mock_issue.uuid = '550e8400-e29b-41d4-a716-446655440000'
    mock_issue.tracking_number = 'SAFE-260728-ABC123'
    mock_issue.issue_type = 'bug'
    mock_issue.category = 'frontend'
    mock_issue.severity = 'medium'
    mock_issue.priority = 'normal'
    mock_issue.status = 'new'
    mock_issue.title = 'Test issue'
    mock_issue.description = 'Description'
    mock_issue.is_anonymous = False
    mock_issue.is_spam = False
    mock_issue.labels = ['ui']
    mock_issue.created_at = None
    mock_issue.updated_at = None
    mock_issue.steps_to_reproduce = None
    mock_issue.expected_behavior = None
    mock_issue.actual_behavior = None
    mock_issue.environment = None
    mock_issue.browser_info = None
    mock_issue.device_info = None
    mock_issue.os_info = None
    mock_issue.app_version = None
    mock_issue.attachments = None
    mock_issue.screenshot_urls = None
    mock_issue.screen_recording_url = None
    mock_issue.logs = None
    mock_issue.system_info = None
    mock_issue.assignee = None
    mock_issue.milestone = None
    mock_issue.duplicate_of = None
    mock_issue.duplicate_score = None
    mock_issue.spam_reason = None
    mock_issue.ai_category = None
    mock_issue.ai_summary = None
    mock_issue.ai_suggested_fix = None
    mock_issue.ai_confidence = None
    mock_issue.github_issue_url = None
    mock_issue.github_issue_number = None
    mock_issue.github_discussion_url = None
    mock_issue.reporter_name = None
    mock_issue.reporter_email = None
    mock_issue.sla_response_at = None
    mock_issue.sla_resolution_at = None
    mock_issue.resolved_at = None
    mock_result.scalar_one_or_none.return_value = mock_issue

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await issue_service.get_issue(db=mock_db, issue_uuid='550e8400-e29b-41d4-a716-446655440000')

    assert result is not None
    assert result.title == 'Test issue'


@pytest.mark.asyncio
async def test_get_issue_not_found(issue_service: IssueService) -> None:
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await issue_service.get_issue(db=mock_db, issue_uuid='nonexistent')

    assert result is None


@pytest.mark.asyncio
async def test_get_issue_by_tracking(issue_service: IssueService) -> None:
    mock_result = MagicMock()
    mock_issue = MagicMock(spec=IssueReport)
    mock_issue.uuid = '550e8400-e29b-41d4-a716-446655440000'
    mock_issue.tracking_number = 'SAFE-260728-ABC123'
    mock_issue.issue_type = 'bug'
    mock_issue.category = 'frontend'
    mock_issue.severity = 'medium'
    mock_issue.priority = 'normal'
    mock_issue.status = 'new'
    mock_issue.title = 'Test issue'
    mock_issue.description = 'Description'
    mock_issue.is_anonymous = False
    mock_issue.is_spam = False
    mock_issue.labels = ['ui']
    mock_issue.created_at = None
    mock_issue.updated_at = None
    mock_issue.steps_to_reproduce = None
    mock_issue.expected_behavior = None
    mock_issue.actual_behavior = None
    mock_issue.environment = None
    mock_issue.browser_info = None
    mock_issue.device_info = None
    mock_issue.os_info = None
    mock_issue.app_version = None
    mock_issue.attachments = None
    mock_issue.screenshot_urls = None
    mock_issue.screen_recording_url = None
    mock_issue.logs = None
    mock_issue.system_info = None
    mock_issue.assignee = None
    mock_issue.milestone = None
    mock_issue.duplicate_of = None
    mock_issue.duplicate_score = None
    mock_issue.spam_reason = None
    mock_issue.ai_category = None
    mock_issue.ai_summary = None
    mock_issue.ai_suggested_fix = None
    mock_issue.ai_confidence = None
    mock_issue.github_issue_url = None
    mock_issue.github_issue_number = None
    mock_issue.github_discussion_url = None
    mock_issue.reporter_name = None
    mock_issue.reporter_email = None
    mock_issue.sla_response_at = None
    mock_issue.sla_resolution_at = None
    mock_issue.resolved_at = None
    mock_result.scalar_one_or_none.return_value = mock_issue
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await issue_service.get_issue_by_tracking(db=mock_db, tracking_number='SAFE-260728-ABC123')

    assert result is not None


@pytest.mark.asyncio
async def test_update_issue(issue_service: IssueService) -> None:
    mock_issue = MagicMock(spec=IssueReport)
    mock_issue.uuid = '550e8400-e29b-41d4-a716-446655440000'
    mock_issue.tracking_number = 'SAFE-260728-ABC123'
    mock_issue.issue_type = 'bug'
    mock_issue.category = 'frontend'
    mock_issue.severity = 'medium'
    mock_issue.priority = 'normal'
    mock_issue.status = 'new'
    mock_issue.title = 'Test issue'
    mock_issue.description = 'Description'
    mock_issue.is_anonymous = False
    mock_issue.is_spam = False
    mock_issue.labels = ['ui']
    mock_issue.created_at = None
    mock_issue.updated_at = None
    mock_issue.steps_to_reproduce = None
    mock_issue.expected_behavior = None
    mock_issue.actual_behavior = None
    mock_issue.environment = None
    mock_issue.browser_info = None
    mock_issue.device_info = None
    mock_issue.os_info = None
    mock_issue.app_version = None
    mock_issue.attachments = None
    mock_issue.screenshot_urls = None
    mock_issue.screen_recording_url = None
    mock_issue.logs = None
    mock_issue.system_info = None
    mock_issue.assignee = None
    mock_issue.milestone = None
    mock_issue.duplicate_of = None
    mock_issue.duplicate_score = None
    mock_issue.spam_reason = None
    mock_issue.ai_category = None
    mock_issue.ai_summary = None
    mock_issue.ai_suggested_fix = None
    mock_issue.ai_confidence = None
    mock_issue.github_issue_url = None
    mock_issue.github_issue_number = None
    mock_issue.github_discussion_url = None
    mock_issue.reporter_name = None
    mock_issue.reporter_email = None
    mock_issue.sla_response_at = None
    mock_issue.sla_resolution_at = None
    mock_issue.resolved_at = None

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_issue
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    update = UpdateIssueRequest(status=IssueStatus.in_progress, assignee='dev-user')
    result = await issue_service.update_issue(db=mock_db, issue_uuid='550e8400-e29b-41d4-a716-446655440000', request=update)

    assert result is not None


@pytest.mark.asyncio
async def test_update_issue_not_found(issue_service: IssueService) -> None:
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    update = UpdateIssueRequest(status=IssueStatus.resolved)
    result = await issue_service.update_issue(db=mock_db, issue_uuid='nonexistent', request=update)

    assert result is None


@pytest.mark.asyncio
async def test_mark_spam(issue_service: IssueService) -> None:
    mock_issue = MagicMock(spec=IssueReport)
    mock_issue.uuid = '550e8400-e29b-41d4-a716-446655440000'
    mock_issue.tracking_number = 'SAFE-260728-ABC123'
    mock_issue.issue_type = 'bug'
    mock_issue.category = 'frontend'
    mock_issue.severity = 'medium'
    mock_issue.priority = 'normal'
    mock_issue.status = 'new'
    mock_issue.title = 'Spam issue'
    mock_issue.description = 'Buy now! Limited offer!'
    mock_issue.is_anonymous = True
    mock_issue.is_spam = False
    mock_issue.labels = []
    mock_issue.created_at = None
    mock_issue.updated_at = None
    mock_issue.steps_to_reproduce = None
    mock_issue.expected_behavior = None
    mock_issue.actual_behavior = None
    mock_issue.environment = None
    mock_issue.browser_info = None
    mock_issue.device_info = None
    mock_issue.os_info = None
    mock_issue.app_version = None
    mock_issue.attachments = None
    mock_issue.screenshot_urls = None
    mock_issue.screen_recording_url = None
    mock_issue.logs = None
    mock_issue.system_info = None
    mock_issue.assignee = None
    mock_issue.milestone = None
    mock_issue.duplicate_of = None
    mock_issue.duplicate_score = None
    mock_issue.spam_reason = None
    mock_issue.ai_category = None
    mock_issue.ai_summary = None
    mock_issue.ai_suggested_fix = None
    mock_issue.ai_confidence = None
    mock_issue.github_issue_url = None
    mock_issue.github_issue_number = None
    mock_issue.github_discussion_url = None
    mock_issue.reporter_name = None
    mock_issue.reporter_email = None
    mock_issue.sla_response_at = None
    mock_issue.sla_resolution_at = None
    mock_issue.resolved_at = None

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_issue
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    result = await issue_service.mark_spam(db=mock_db, issue_uuid='550e8400-e29b-41d4-a716-446655440000')
    assert result is not None


@pytest.mark.asyncio
async def test_mark_duplicate(issue_service: IssueService) -> None:
    mock_issue = MagicMock(spec=IssueReport)
    mock_issue.uuid = '550e8400-e29b-41d4-a716-446655440000'
    mock_issue.tracking_number = 'SAFE-260728-ABC123'
    mock_issue.issue_type = 'bug'
    mock_issue.category = 'frontend'
    mock_issue.severity = 'medium'
    mock_issue.priority = 'normal'
    mock_issue.status = 'new'
    mock_issue.title = 'Duplicate issue'
    mock_issue.description = 'This is a duplicate'
    mock_issue.is_anonymous = False
    mock_issue.is_spam = False
    mock_issue.labels = []
    mock_issue.created_at = None
    mock_issue.updated_at = None
    mock_issue.steps_to_reproduce = None
    mock_issue.expected_behavior = None
    mock_issue.actual_behavior = None
    mock_issue.environment = None
    mock_issue.browser_info = None
    mock_issue.device_info = None
    mock_issue.os_info = None
    mock_issue.app_version = None
    mock_issue.attachments = None
    mock_issue.screenshot_urls = None
    mock_issue.screen_recording_url = None
    mock_issue.logs = None
    mock_issue.system_info = None
    mock_issue.assignee = None
    mock_issue.milestone = None
    mock_issue.duplicate_of = None
    mock_issue.duplicate_score = None
    mock_issue.spam_reason = None
    mock_issue.ai_category = None
    mock_issue.ai_summary = None
    mock_issue.ai_suggested_fix = None
    mock_issue.ai_confidence = None
    mock_issue.github_issue_url = None
    mock_issue.github_issue_number = None
    mock_issue.github_discussion_url = None
    mock_issue.reporter_name = None
    mock_issue.reporter_email = None
    mock_issue.sla_response_at = None
    mock_issue.sla_resolution_at = None
    mock_issue.resolved_at = None

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_issue
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    result = await issue_service.mark_duplicate(
        db=mock_db,
        issue_uuid='550e8400-e29b-41d4-a716-446655440000',
        original_uuid='660e8400-e29b-41d4-a716-446655440001',
    )
    assert result is not None


@pytest.mark.asyncio
async def test_detect_spam_keywords(issue_service: IssueService) -> None:
    mock_issue = MagicMock(spec=IssueReport)
    mock_issue.title = 'Buy now!'
    mock_issue.description = 'Click here for free money!!!'
    mock_issue.reporter_email = 'spam@tempmail.com'

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_issue
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    is_spam, reason = await issue_service.detect_spam(db=mock_db, issue_uuid='some-uuid')
    assert is_spam is True
    assert reason is not None


@pytest.mark.asyncio
async def test_detect_spam_clean(issue_service: IssueService) -> None:
    mock_issue = MagicMock(spec=IssueReport)
    mock_issue.title = 'Normal bug report'
    mock_issue.description = 'The button does not work on Safari'
    mock_issue.reporter_email = 'user@example.com'

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_issue
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    is_spam, reason = await issue_service.detect_spam(db=mock_db, issue_uuid='some-uuid')
    assert is_spam is False


@pytest.mark.asyncio
async def test_find_duplicates(issue_service: IssueService) -> None:
    mock_source = MagicMock(spec=IssueReport)
    mock_source.uuid = '550e8400-e29b-41d4-a716-446655440000'
    mock_source.title = 'Button not working'
    mock_source.description = 'Submit button fails'
    mock_source.issue_type = 'bug'

    mock_candidate = MagicMock(spec=IssueReport)
    mock_candidate.uuid = '660e8400-e29b-41d4-a716-446655440001'
    mock_candidate.tracking_number = 'SAFE-260728-DEF456'
    mock_candidate.title = 'Submit button not working'
    mock_candidate.issue_type = 'bug'

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_source
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    mock_all = MagicMock()
    mock_all.scalars.return_value.all.return_value = [mock_candidate]

    async def mock_execute_side_effect(*args, **kwargs):
        if 'scalar_one_or_none' in str(type(args[0])):
            return mock_result
        return mock_all

    mock_db.execute = AsyncMock(side_effect=mock_execute_side_effect)

    duplicates = await issue_service.find_duplicates(db=mock_db, issue_uuid='550e8400-e29b-41d4-a716-446655440000')
    assert isinstance(duplicates, list)


@pytest.mark.asyncio
async def test_set_sla(issue_service: IssueService) -> None:
    mock_issue = MagicMock(spec=IssueReport)
    mock_issue.uuid = '550e8400-e29b-41d4-a716-446655440000'
    mock_issue.tracking_number = 'SAFE-260728-ABC123'
    mock_issue.issue_type = 'bug'
    mock_issue.category = 'frontend'
    mock_issue.severity = 'critical'
    mock_issue.priority = 'high'
    mock_issue.status = 'new'
    mock_issue.title = 'Critical issue'
    mock_issue.description = 'Critical bug'
    mock_issue.is_anonymous = False
    mock_issue.is_spam = False
    mock_issue.labels = []
    mock_issue.created_at = None
    mock_issue.updated_at = None
    mock_issue.steps_to_reproduce = None
    mock_issue.expected_behavior = None
    mock_issue.actual_behavior = None
    mock_issue.environment = None
    mock_issue.browser_info = None
    mock_issue.device_info = None
    mock_issue.os_info = None
    mock_issue.app_version = None
    mock_issue.attachments = None
    mock_issue.screenshot_urls = None
    mock_issue.screen_recording_url = None
    mock_issue.logs = None
    mock_issue.system_info = None
    mock_issue.assignee = None
    mock_issue.milestone = None
    mock_issue.duplicate_of = None
    mock_issue.duplicate_score = None
    mock_issue.spam_reason = None
    mock_issue.ai_category = None
    mock_issue.ai_summary = None
    mock_issue.ai_suggested_fix = None
    mock_issue.ai_confidence = None
    mock_issue.github_issue_url = None
    mock_issue.github_issue_number = None
    mock_issue.github_discussion_url = None
    mock_issue.reporter_name = None
    mock_issue.reporter_email = None
    mock_issue.sla_response_at = None
    mock_issue.sla_resolution_at = None
    mock_issue.resolved_at = None

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_issue
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    result = await issue_service.set_sla(db=mock_db, issue_uuid='550e8400-e29b-41d4-a716-446655440000')
    assert result is not None


@pytest.mark.asyncio
async def test_issue_to_list_item(issue_service: IssueService) -> None:
    mock_issue = MagicMock(spec=IssueReport)
    mock_issue.uuid = '550e8400-e29b-41d4-a716-446655440000'
    mock_issue.tracking_number = 'SAFE-260728-ABC123'
    mock_issue.issue_type = 'bug'
    mock_issue.category = 'frontend'
    mock_issue.severity = 'medium'
    mock_issue.priority = 'normal'
    mock_issue.status = 'new'
    mock_issue.title = 'Test'
    mock_issue.labels = ['ui']
    mock_issue.is_anonymous = False
    mock_issue.is_spam = False
    mock_issue.duplicate_of = None
    mock_issue.ai_category = None
    mock_issue.assignee = None
    mock_issue.milestone = None
    mock_issue.github_issue_number = None
    mock_issue.reporter_name = None
    mock_issue.created_at = None
    mock_issue.updated_at = None

    item = issue_service._issue_to_list_item(mock_issue)
    assert item.title == 'Test'
    assert item.tracking_number == 'SAFE-260728-ABC123'
    assert item.status == 'new'


@pytest.mark.asyncio
async def test_generate_tracking_number_format() -> None:
    from services.issue_service import _generate_tracking_number
    tn = _generate_tracking_number()
    assert tn.startswith('SAFE-')
    assert len(tn) == 17
